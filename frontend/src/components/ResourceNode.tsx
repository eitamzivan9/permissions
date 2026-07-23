import { useState } from "react";
import type { CatalogItem, ResourceType } from "../api/client";
import RoleBadge from "./RoleBadge";
import ManageAccessModal from "./ManageAccessModal";

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
  const hasChildren = item.children.length > 0;

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
          {item.can_manage && (
            <button
              type="button"
              onClick={() => setIsManaging(true)}
              className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
            >
              Manage access
            </button>
          )}
        </div>
      </div>

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
    </div>
  );
}
