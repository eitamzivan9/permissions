import type { DragEvent } from "react";
import { useState } from "react";
import type { CatalogItem, ResourceType } from "../api/client";
import { moveResource } from "../api/client";
import { TYPE_LABELS } from "../lib/resourceTypeMeta";
import ResourceInfoPanel from "./ResourceInfoPanel";
import RoleBadge from "./RoleBadge";

// Workspace/Folder/Map subtrees can be large, so those levels start collapsed
// — the caller clicks in to drill down. Group (just a handful of Layers) still
// starts open, since there's nothing large to hide there.
const DEFAULT_COLLAPSED_TYPES = new Set<ResourceType>(["workspace", "folder", "map"]);

// The dataTransfer payload a drag-start writes and a drop reads back — see
// handleDragStart/handleDrop below.
interface DragPayload {
  id: string;
}

interface ResourceNodeProps {
  item: CatalogItem;
  depth: number;
  onChanged: () => void;
}

// One recursive component for all 5 resource levels — mirrors the backend's
// single Resource/CatalogItem model instead of a MapCard/LayerChip pair.
export default function ResourceNode({ item, depth, onChanged }: ResourceNodeProps) {
  const [isExpanded, setIsExpanded] = useState(() => !DEFAULT_COLLAPSED_TYPES.has(item.type));
  const [isInfoOpen, setIsInfoOpen] = useState(false);
  const [isDropTarget, setIsDropTarget] = useState(false);
  const [moveError, setMoveError] = useState<string | null>(null);
  const hasChildren = item.children.length > 0;

  // Move is drag-and-drop only (no picker modal) — a node may be dragged
  // only when the caller is Admin there, same gate the old "Move" button
  // used; the server re-checks on PATCH /resources/{id}/move regardless, so
  // this is purely a UX hint. Every node (draggable or not) is a valid drop
  // TARGET — legality (type pairing, cycle-safety) stays server-authoritative,
  // surfaced here only as an inline error on a rejected drop.
  const isDraggable = item.effective_role === "admin";

  function handleDragStart(event: DragEvent<HTMLDivElement>) {
    const payload: DragPayload = { id: item.id };
    event.dataTransfer.setData("application/json", JSON.stringify(payload));
    event.dataTransfer.effectAllowed = "move";
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    setIsDropTarget(true);
  }

  function handleDragLeave() {
    setIsDropTarget(false);
  }

  async function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDropTarget(false);
    let payload: DragPayload;
    try {
      payload = JSON.parse(event.dataTransfer.getData("application/json")) as DragPayload;
    } catch {
      return;
    }
    if (!payload.id || payload.id === item.id) return;

    setMoveError(null);
    try {
      await moveResource({ resourceId: payload.id, newParentId: item.id });
      onChanged();
    } catch (error: unknown) {
      setMoveError(error instanceof Error ? error.message : "Failed to move the resource.");
    }
  }

  return (
    <div className={depth > 0 ? "border-l border-slate-200 pl-3" : undefined}>
      <div
        draggable={isDraggable}
        onDragStart={isDraggable ? handleDragStart : undefined}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`flex items-center justify-between gap-3 rounded-md px-3 py-2 ${
          depth === 0 ? "border border-slate-200 bg-white shadow-sm" : "bg-slate-50"
        } ${isDraggable ? "cursor-grab active:cursor-grabbing" : ""} ${
          isDropTarget ? "ring-2 ring-inset ring-slate-400" : ""
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
          <button
            type="button"
            onClick={() => setIsInfoOpen(true)}
            className="flex h-6 w-6 items-center justify-center rounded-full border border-slate-300 text-xs font-semibold text-slate-500 hover:bg-slate-100"
            aria-label={`Actions for ${item.name}`}
            title="Actions"
          >
            i
          </button>
        </div>
      </div>

      {moveError && (
        <p className="mt-1 rounded-md bg-red-50 px-3 py-1.5 text-xs text-red-700">{moveError}</p>
      )}

      {hasChildren && isExpanded && (
        <div className="mt-2 space-y-2 pl-4">
          {item.children.map((child) => (
            <ResourceNode key={child.id} item={child} depth={depth + 1} onChanged={onChanged} />
          ))}
        </div>
      )}

      {isInfoOpen && (
        <ResourceInfoPanel item={item} onClose={() => setIsInfoOpen(false)} onChanged={onChanged} />
      )}
    </div>
  );
}
