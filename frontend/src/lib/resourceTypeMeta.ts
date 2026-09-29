import type { ResourceType } from "../api/client";

// Display labels for resource types are translated — see TYPE_LABEL_KEYS in
// i18n/labels.ts.

// Workspace/Folder/Group are this server's own organizational structure —
// deleting one is real (only once empty). Map/Layer represent data owned by
// another system: the frontend never deletes the Resource itself, only the
// current user's own access to it ("Remove access" instead of "Delete").
export const ORGANIZATIONAL_TYPES = new Set<ResourceType>(["workspace", "folder", "group"]);
