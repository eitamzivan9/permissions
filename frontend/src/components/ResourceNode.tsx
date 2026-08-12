import { useState } from "react";
import type { CatalogItem, ResourceType } from "../api/client";
import { deleteGrant, deleteResource, roleAtLeast } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import RoleBadge from "./RoleBadge";
import ManageAccessModal from "./ManageAccessModal";
import CreateResourceModal from "./CreateResourceModal";
import MoveResourceModal from "./MoveResourceModal";
import RestrictionsModal from "./RestrictionsModal";

// Workspace/Folder/Group are this server's own organizational structure —
// deleting one is real (only once empty). Map/Layer represent data owned by
// another system: the frontend never deletes the Resource itself, only the
// current user's own access to it (see "Remove access" below).
const ORGANIZATIONAL_TYPES = new Set<ResourceType>(["workspace", "folder", "group"]);

// One recursive component for all 5 resource levels — mirrors the backend's
// single Resource/CatalogItem model instead of a MapCard/LayerChip pair.
const TYPE_LABELS: Record<ResourceType, string> = {
  workspace: "Workspace",
  folder: "Folder",
  map: "Map",
  group: "Group",
  layer: "Layer",
};

// Workspace/Folder/Map subtrees can be large, so those levels start collapsed
// — the caller clicks in to drill down. Group (just a handful of Layers) still
// starts open, since there's nothing large to hide there.
const DEFAULT_COLLAPSED_TYPES = new Set<ResourceType>(["workspace", "folder", "map"]);

interface ResourceNodeProps {
  item: CatalogItem;
  depth: number;
  onChanged: () => void;
}

export default function ResourceNode({ item, depth, onChanged }: ResourceNodeProps) {
  const { user } = useAuth();
  const [isExpanded, setIsExpanded] = useState(() => !DEFAULT_COLLAPSED_TYPES.has(item.type));
  const [isManaging, setIsManaging] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isRestricting, setIsRestricting] = useState(false);
  const [isMoving, setIsMoving] = useState(false);
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const hasChildren = item.children.length > 0;
  const isOrganizational = ORGANIZATIONAL_TYPES.has(item.type);
  // A Layer is always a leaf, so it's never a valid parent for a new child.
  const canCreateHere = item.type !== "layer" && roleAtLeast(item.effective_role, "editor");
  // Mirrors the backend's restrictions_router check exactly: Admin only
  // (SUPER_EDITOR already resolves to effective_role "admin", so it's covered).
  const canRestrictHere = item.effective_role === "admin";
  // Same Admin-only gate as the backend's ResourceService.move() source check.
  const canMoveHere = item.effective_role === "admin";
  // Workspace/Folder/Group only ever hard-delete when empty — same Admin-only
  // gate as the backend's ResourceService.delete() check.
  const canDeleteHere = isOrganizational && item.effective_role === "admin";
  // Map/Layer: this server doesn't own that data, so there's no "delete" from
  // here — only revoking the CURRENT user's own access, at any role.
  const canRemoveAccessHere = !isOrganizational && item.effective_role !== null;

  async function handleDelete() {
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteResource(item.id);
      onChanged();
      // A successful delete normally removes this node from the tree
      // entirely (unmounting it), but ResourceNode is keyed by item.id, so
      // if it's still around after the refetch (e.g. the parent hasn't
      // re-rendered yet), local state must still be reset — otherwise the
      // button gets stuck on "Deleting…" forever, same failure mode as
      // "Remove access" below (which never unmounts, since the resource
      // itself stays put).
      setIsDeleting(false);
      setIsConfirmingDelete(false);
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
      // Unlike delete, this node normally stays in the tree (the resource
      // itself is untouched) — the confirm/loading state MUST be reset here
      // or it's stuck on "Removing…" forever, since React keeps the same
      // component instance alive across the refetch (same key).
      setIsDeleting(false);
      setIsConfirmingDelete(false);
    } catch (error: unknown) {
      setDeleteError(error instanceof Error ? error.message : "Failed to remove access.");
      setIsDeleting(false);
      setIsConfirmingDelete(false);
    }
  }

  return (
    <div className={depth > 0 ? "border-l border-slate-200 pl-3" : undefined}>
      <div
        className={`flex items-center justify-between gap-3 rounded-md px-3 py-2 ${
          depth === 0 ? "border border-slate-200 bg-white shadow-sm" : "bg-slate-50"
        }`}
      >
        <div className="flex min-w-0 items-center gap-2">
          {hasChildren ? (
            <button
              type="button"
              onClick={() => setIsExpanded((expanded) => !expanded)}
              className="shrink-0 text-slate-400 hover:text-slate-600"
              aria-label={isExpanded ? "Collapse" : "Expand"}
            >
              {isExpanded ? "▾" : "▸"}
            </button>
          ) : (
            <span className="w-4 shrink-0" />
          )}
          <span className="shrink-0 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-slate-500">
            {TYPE_LABELS[item.type]}
          </span>
          <span className="truncate text-sm font-medium text-slate-900">{item.name}</span>
          {!item.effective_role && item.can_fetch && (
            <span
              className="shrink-0 text-xs text-slate-400"
              title="No role here, but reachable via at least one accessible child"
            >
              (reachable)
            </span>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <RoleBadge role={item.effective_role} />
          {canCreateHere && (
            <button
              type="button"
              onClick={() => setIsCreating(true)}
              className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
              aria-label={`Create resource inside ${item.name}`}
            >
              + Create
            </button>
          )}
          {item.can_manage && (
            <button
              type="button"
              onClick={() => setIsManaging(true)}
              className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
            >
              Manage access
            </button>
          )}
          {canRestrictHere && (
            <button
              type="button"
              onClick={() => setIsRestricting(true)}
              className="rounded-md border border-amber-300 px-2 py-1 text-xs font-medium text-amber-700 hover:bg-amber-50"
            >
              Restrictions
            </button>
          )}
          {canMoveHere && (
            <button
              type="button"
              onClick={() => setIsMoving(true)}
              className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
            >
              Move
            </button>
          )}
          {(canDeleteHere || canRemoveAccessHere) && !isConfirmingDelete && (
            <button
              type="button"
              onClick={() => setIsConfirmingDelete(true)}
              className="rounded-md border border-red-300 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50"
            >
              {canDeleteHere ? "Delete" : "Remove access"}
            </button>
          )}
          {(canDeleteHere || canRemoveAccessHere) && isConfirmingDelete && (
            <span className="flex shrink-0 items-center gap-1.5">
              <span className="text-xs text-red-700">
                {canDeleteHere ? "Delete this?" : "Remove your access to this?"}
              </span>
              <button
                type="button"
                onClick={canDeleteHere ? handleDelete : handleRemoveAccess}
                disabled={isDeleting}
                className="rounded-md bg-red-600 px-2 py-1 text-xs font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isDeleting ? "Removing…" : "Confirm"}
              </button>
              <button
                type="button"
                onClick={() => setIsConfirmingDelete(false)}
                disabled={isDeleting}
                className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Cancel
              </button>
            </span>
          )}
        </div>
      </div>

      {deleteError && (
        <p className="mt-1 rounded-md bg-red-50 px-3 py-1.5 text-xs text-red-700">{deleteError}</p>
      )}

      {hasChildren && isExpanded && (
        <div className="mt-2 space-y-2 pl-4">
          {item.children.map((child) => (
            <ResourceNode key={child.id} item={child} depth={depth + 1} onChanged={onChanged} />
          ))}
        </div>
      )}

      {isManaging && (
        <ManageAccessModal
          resourceId={item.id}
          resourceName={item.name}
          onClose={() => setIsManaging(false)}
          onChanged={onChanged}
        />
      )}

      {isCreating && (
        <CreateResourceModal
          parentId={item.id}
          parentName={item.name}
          onClose={() => setIsCreating(false)}
          onCreated={onChanged}
        />
      )}

      {isRestricting && (
        <RestrictionsModal
          resourceId={item.id}
          resourceName={item.name}
          onClose={() => setIsRestricting(false)}
          onChanged={onChanged}
        />
      )}

      {isMoving && (
        <MoveResourceModal
          resourceId={item.id}
          resourceName={item.name}
          onClose={() => setIsMoving(false)}
          onChanged={onChanged}
        />
      )}
    </div>
  );
}
