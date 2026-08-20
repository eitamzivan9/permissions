import type { ResourceType } from "../api/client";

// One shared source for these two resource-type facts — ResourceNode and
// ResourceInfoPanel both need them, and this keeps them from drifting apart.
export const TYPE_LABELS: Record<ResourceType, string> = {
  workspace: "Workspace",
  folder: "Folder",
  map: "Map",
  group: "Group",
  layer: "Layer",
};

// Workspace/Folder/Group are this server's own organizational structure —
// deleting one is real (only once empty). Map/Layer represent data owned by
// another system: the frontend never deletes the Resource itself, only the
// current user's own access to it ("Remove access" instead of "Delete").
export const ORGANIZATIONAL_TYPES = new Set<ResourceType>(["workspace", "folder", "group"]);
