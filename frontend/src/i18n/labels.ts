import type { ResourceType, Role } from "../api/client";
import type { MessageKey } from "./en";

// Typed bridges from backend enum values to translation keys, so callers
// never build a key string by hand (and a new enum value fails the build
// until it has a label).
export const ROLE_LABEL_KEYS: Record<Role, MessageKey> = {
  viewer: "role.viewer",
  editor: "role.editor",
  manager: "role.manager",
  admin: "role.admin",
};

export const TYPE_LABEL_KEYS: Record<ResourceType, MessageKey> = {
  workspace: "type.workspace",
  folder: "type.folder",
  map: "type.map",
  group: "type.group",
  layer: "type.layer",
};
