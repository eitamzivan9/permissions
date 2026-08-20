import { useEffect, useState } from "react";
import type { CatalogItem, GranteeInfo } from "../api/client";
import { deleteGrant, deleteResource, getResourceAdmins, roleAtLeast } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ORGANIZATIONAL_TYPES, TYPE_LABELS } from "../lib/resourceTypeMeta";
import CreateResourceModal from "./CreateResourceModal";
import ManageAccessModal from "./ManageAccessModal";
import RestrictionsModal from "./RestrictionsModal";

interface ResourceInfoPanelProps {
  item: CatalogItem;
  onClose: () => void;
  /** Called after a successful grant/restriction/create/delete so the caller can refetch the catalog. */
  onChanged: () => void;
}

type SubView = "menu" | "manage" | "create" | "restrict";

// The single entry point for every per-resource action (Create, Manage
// access, Restrictions, Delete/Remove access) plus the "who has access"
// lookup — one info button per ResourceNode opens this instead of a row of
// individual buttons. Each action still reuses the existing modal
// components unchanged (same resourceId/resourceName/onClose/onChanged
// props they always took); this panel just decides which one to show and,
// once one is open, hands off to it fully (closing this panel too) rather
// than returning to a menu — mirrors the one-hop flow the old per-button
// row already had.
export default function ResourceInfoPanel({ item, onClose, onChanged }: ResourceInfoPanelProps) {
  const { user } = useAuth();
  const [subView, setSubView] = useState<SubView>("menu");
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [admins, setAdmins] = useState<GranteeInfo[] | null>(null);
  const [isLoadingAdmins, setIsLoadingAdmins] = useState(false);

  const hasChildren = item.children.length > 0;
  const isOrganizational = ORGANIZATIONAL_TYPES.has(item.type);
  // A Layer is always a leaf, so it's never a valid parent for a new child.
  const canCreateHere = item.type !== "layer" && roleAtLeast(item.effective_role, "editor");
  // Mirrors the backend's restrictions_router check exactly: Admin only
  // (SUPER_EDITOR already resolves to effective_role "admin", so it's covered).
  const canRestrictHere = item.effective_role === "admin";
  // Workspace/Folder/Group only ever hard-delete when empty — same Admin-only
  // gate as the backend's ResourceService.delete() check, PLUS the emptiness
  // check itself done client-side so the action is never offered only to fail.
  const canDeleteHere = isOrganizational && item.effective_role === "admin" && !hasChildren;
  const deleteBlockedByChildren = isOrganizational && item.effective_role === "admin" && hasChildren;
  // Map/Layer: this server doesn't own that data, so there's no "delete" from
  // here — only revoking the CURRENT user's own access, at any role.
  const canRemoveAccessHere = !isOrganizational && item.effective_role !== null;

  useEffect(() => {
    if (item.effective_role !== null) return;
    let cancelled = false;
    setIsLoadingAdmins(true);
    getResourceAdmins(item.id)
      .then((result) => {
        if (!cancelled) setAdmins(result);
      })
      .catch(() => {
        if (!cancelled) setAdmins([]);
      })
      .finally(() => {
        if (!cancelled) setIsLoadingAdmins(false);
      });
    return () => {
      cancelled = true;
    };
  }, [item.id, item.effective_role]);

  async function handleDelete() {
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteResource(item.id);
      onChanged();
      onClose();
    } catch (error: unknown) {
      setDeleteError(error instanceof Error ? error.message : "Failed to delete.");
      setIsDeleting(false);
      setIsConfirmingDelete(false);
    }
  }

  async function handleRemoveAccess() {
    if (!user) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteGrant({ resourceId: item.id, granteeType: "user", granteeId: user.id });
      onChanged();
      onClose();
    } catch (error: unknown) {
      setDeleteError(error instanceof Error ? error.message : "Failed to remove access.");
      setIsDeleting(false);
      setIsConfirmingDelete(false);
    }
  }

  if (subView === "manage") {
    return (
      <ManageAccessModal
        resourceId={item.id}
        resourceName={item.name}
        onClose={onClose}
        onChanged={onChanged}
      />
    );
  }

  if (subView === "create") {
    return (
      <CreateResourceModal
        parentId={item.id}
        parentName={item.name}
        onClose={onClose}
        onCreated={onChanged}
      />
    );
  }

  if (subView === "restrict") {
    return (
      <RestrictionsModal
        resourceId={item.id}
        resourceName={item.name}
        onClose={onClose}
        onChanged={onChanged}
      />
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-lg bg-white p-5 shadow-lg"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-slate-500">
              {TYPE_LABELS[item.type]}
            </span>
            <h3 className="mt-1 truncate text-base font-semibold text-slate-900">{item.name}</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-md px-2 py-1 text-sm text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {item.effective_role === null && (
          <div className="mt-4 rounded-md bg-slate-50 p-3 text-sm">
            <p className="font-medium text-slate-700">You don't have access to this resource.</p>
            {isLoadingAdmins && <p className="mt-1 text-slate-500">Looking up who to ask…</p>}
            {!isLoadingAdmins && admins !== null && admins.length === 0 && (
              <p className="mt-1 text-slate-500">No one currently has Admin access here to ask.</p>
            )}
            {!isLoadingAdmins && admins !== null && admins.length > 0 && (
              <>
                <p className="mt-1 text-slate-500">Ask one of the following for access:</p>
                <ul className="mt-1 space-y-0.5">
                  {admins.map((admin) => (
                    <li key={`${admin.grantee_type}-${admin.id}`} className="text-slate-700">
                      {admin.name}
                      {admin.grantee_type === "team" && (
                        <span className="ml-1 text-xs text-slate-400">(team)</span>
                      )}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}

        <div className="mt-4 space-y-2">
          {canCreateHere && (
            <button
              type="button"
              onClick={() => setSubView("create")}
              className="block w-full rounded-md border border-slate-300 px-3 py-2 text-left text-sm font-medium text-slate-700 hover:bg-slate-100"
            >
              + Create
            </button>
          )}
          {item.can_manage && (
            <button
              type="button"
              onClick={() => setSubView("manage")}
              className="block w-full rounded-md border border-slate-300 px-3 py-2 text-left text-sm font-medium text-slate-700 hover:bg-slate-100"
            >
              Manage access
            </button>
          )}
          {canRestrictHere && (
            <button
              type="button"
              onClick={() => setSubView("restrict")}
              className="block w-full rounded-md border border-amber-300 px-3 py-2 text-left text-sm font-medium text-amber-700 hover:bg-amber-50"
            >
              Restrictions
            </button>
          )}

          {(canDeleteHere || canRemoveAccessHere) && !isConfirmingDelete && (
            <button
              type="button"
              onClick={() => setIsConfirmingDelete(true)}
              className="block w-full rounded-md border border-red-300 px-3 py-2 text-left text-sm font-medium text-red-700 hover:bg-red-50"
            >
              {canDeleteHere ? "Delete" : "Remove access"}
            </button>
          )}
          {(canDeleteHere || canRemoveAccessHere) && isConfirmingDelete && (
            <div className="rounded-md border border-red-300 p-3">
              <p className="text-sm text-red-700">
                {canDeleteHere ? "Delete this resource?" : "Remove your access to this resource?"}
              </p>
              <div className="mt-2 flex gap-2">
                <button
                  type="button"
                  onClick={canDeleteHere ? handleDelete : handleRemoveAccess}
                  disabled={isDeleting}
                  className="rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isDeleting ? "Removing…" : "Confirm"}
                </button>
                <button
                  type="button"
                  onClick={() => setIsConfirmingDelete(false)}
                  disabled={isDeleting}
                  className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
          {deleteBlockedByChildren && (
            <p className="text-xs text-slate-400">
              Delete disabled — {item.children.length} item{item.children.length === 1 ? "" : "s"}{" "}
              inside. Remove them first.
            </p>
          )}
          {deleteError && (
            <p className="rounded-md bg-red-50 px-3 py-1.5 text-xs text-red-700">{deleteError}</p>
          )}

          {!canCreateHere &&
            !item.can_manage &&
            !canRestrictHere &&
            !canDeleteHere &&
            !canRemoveAccessHere &&
            !deleteBlockedByChildren && (
              <p className="text-sm text-slate-500">No actions available to you here.</p>
            )}
        </div>
      </div>
    </div>
  );
}
