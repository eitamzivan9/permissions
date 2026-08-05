import { useState } from "react";
import type { CatalogItem, ResourceType } from "../api/client";
import { deleteResource, roleAtLeast } from "../api/client";
import RoleBadge from "./RoleBadge";
import ManageAccessModal from "./ManageAccessModal";
import CreateResourceModal from "./CreateResourceModal";
import RestrictionsModal from "./RestrictionsModal";

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
  const [isExpanded, setIsExpanded] = useState(() => !DEFAULT_COLLAPSED_TYPES.has(item.type));
  const [isManaging, setIsManaging] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isRestricting, setIsRestricting] = useState(false);
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const hasChildren = item.children.length > 0;
  // A Layer is always a leaf, so it's never a valid parent for a new child.
  const canCreateHere = item.type !== "layer" && roleAtLeast(item.effective_role, "editor");
  // Mirrors the backend's restrictions_router check exactly: Admin only
  // (SUPER_EDITOR already resolves to effective_role "admin", so it's covered).
  const canRestrictHere = item.effective_role === "admin";
  // Deleting is at least as destructive as restricting — same Admin-only gate
  // as the backend's ResourceService.delete() check.
  const canDeleteHere = item.effective_role === "admin";

  async function handleDelete() {
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteResource(item.id);
      onChanged();
    } catch (error: unknown) {
      setDeleteError(error instanceof Error ? error.message : "Failed to delete.");
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
          {canDeleteHere && !isConfirmingDelete && (
            <button
              type="button"
              onClick={() => setIsConfirmingDelete(true)}
              className="rounded-md border border-red-300 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50"
            >
              Delete
            </button>
          )}
          {canDeleteHere && isConfirmingDelete && (
            <span className="flex shrink-0 items-center gap-1.5">
              <span className="text-xs text-red-700">
                {hasChildren ? "Delete this and everything inside?" : "Delete this?"}
              </span>
              <button
                type="button"
                onClick={handleDelete}
                disabled={isDeleting}
                className="rounded-md bg-red-600 px-2 py-1 text-xs font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isDeleting ? "Deleting…" : "Confirm"}
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
    </div>
  );
}
