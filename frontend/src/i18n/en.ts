// English UI strings — the source of truth for every translation key, and
// the fallback for any key another language (he.ts) doesn't translate.
// Values are words only: decorative symbols shared by every language
// ("+ " prefixes, "…" suffixes, wrapping parentheses) live in the JSX.
// `{name}` placeholders are filled by format().
// Keys ending in `.one`/`.other` are plural forms, picked by tPlural().
export const en = {
  "lang.switchTo": "עברית",

  "common.close": "Close",
  "common.loading": "Loading",
  "common.cancel": "Cancel",
  "common.confirm": "Confirm",
  "common.create": "Create",
  "common.creating": "Creating",
  "common.applying": "Applying",
  "common.name": "Name",
  "common.role": "Role",
  "common.user": "User",
  "common.team": "Team",
  "common.teamSuffix": "team",
  "common.teamLabel": "Team: {name}",
  "common.unknownUser": "unknown user",
  "common.unknown": "unknown",
  "common.noTeams": "No teams exist yet.",
  "common.userOption": "{name} ({email})",

  "role.viewer": "Viewer",
  "role.editor": "Editor",
  "role.manager": "Manager",
  "role.admin": "Admin",
  "role.none": "No access",

  "type.workspace": "Workspace",
  "type.folder": "Folder",
  "type.map": "Map",
  "type.group": "Group",
  "type.layer": "Layer",

  "login.title": "Permissions Server",
  "login.subtitle": "Mock ADFS sign-in — choose an identity to continue.",
  "login.loadingUsers": "Loading mock users",
  "login.loadUsersFailed": "Failed to load mock users.",
  "login.signInAs": "Sign in as",
  "login.signIn": "Sign in",
  "login.signingIn": "Signing in",
  "login.failed": "Login failed.",

  "permissions.title": "Resource Access",
  "permissions.createTeamWorkspace": "Create team workspace",
  "permissions.logout": "Log out",
  "permissions.searchPlaceholder": "Search by name (any workspace, folder, map, group, or layer)",
  "permissions.loadFailed": "Failed to load the catalog.",
  "permissions.loadMoreFailed": "Failed to load the rest of the catalog.",
  "permissions.noResults": "Nothing matches your search.",
  "permissions.showing.one": "Showing {count} result",
  "permissions.showing.other": "Showing {count} results",
  "permissions.showAll": "Show all",

  "node.collapse": "Collapse",
  "node.expand": "Expand",
  "node.reachable": "reachable",
  "node.reachableHint": "No role here, but reachable via at least one accessible child",
  "node.actions": "Actions",
  "node.actionsFor": "Actions for {name}",
  "node.moveFailed": "Failed to move the resource.",

  "info.noAccess": "You don't have access to this resource.",
  "info.lookingUpAdmins": "Looking up who to ask",
  "info.noAdmins": "No one currently has Admin access here to ask.",
  "info.askAdmins": "Ask one of the following for access:",
  "info.create": "Create",
  "info.manageAccess": "Manage access",
  "info.restrictions": "Restrictions",
  "info.delete": "Delete",
  "info.removeAccess": "Remove access",
  "info.confirmDelete": "Delete this resource?",
  "info.confirmRemoveAccess": "Remove your access to this resource?",
  "info.removing": "Removing",
  "info.deleteBlocked.one": "Delete disabled — {count} item inside. Remove it first.",
  "info.deleteBlocked.other": "Delete disabled — {count} items inside. Remove them first.",
  "info.deleteFailed": "Failed to delete.",
  "info.removeAccessFailed": "Failed to remove access.",
  "info.noActions": "No actions available to you here.",

  "createResource.title": "Create folder",
  "createResource.inside": "Inside",
  "createResource.placeholder": "e.g. Zoning Districts",
  "createResource.failed": "Failed to create the resource.",

  "teamWorkspace.title": "Create team workspace",
  "teamWorkspace.subtitle": "Superuser only",
  "teamWorkspace.placeholder": "e.g. City Planning",
  "teamWorkspace.initialAdmin": "Initial admin",
  "teamWorkspace.loadUsersFailed": "Failed to load users.",
  "teamWorkspace.failed": "Failed to create the workspace.",

  "manageAccess.title": "Manage access",
  "manageAccess.loadFailed": "Failed to load access data.",
  "manageAccess.currentGrants": "Current grants here",
  "manageAccess.revoke": "Revoke",
  "manageAccess.grantAccess": "Grant access",
  "manageAccess.noSubordinates": "You have no subordinates to grant access to.",
  "manageAccess.setSuccess": "Set {role} access.",
  "manageAccess.revokeSuccess": "Grant revoked.",
  "manageAccess.updateFailed": "Failed to update access.",
  "manageAccess.revokeFailed": "Failed to revoke access.",

  "restrictions.title": "Restrictions (whitelist)",
  "restrictions.warning":
    "Adding anyone here turns this resource (and everything below it) into a whitelist: only grantees listed below keep access, even ones who currently have an Admin grant. This overrides ordinary access grants for everyone except a system Super Editor or Super Viewer.",
  "restrictions.loadFailed": "Failed to load restrictions.",
  "restrictions.current": "Currently whitelisted here",
  "restrictions.clearAll": "Clear all",
  "restrictions.remove": "Remove",
  "restrictions.none": "No whitelist here yet — access is governed by ordinary grants only.",
  "restrictions.adminToday": "Admin here today",
  "restrictions.adminTodayHint":
    "Not on a whitelist yet — will stay whitelisted automatically once the first restriction is added here.",
  "restrictions.add": "Add to whitelist",
  "restrictions.noUsers": "No users available.",
  "restrictions.addSuccess": "Added {role} to the whitelist.",
  "restrictions.removeSuccess": "Removed from the whitelist.",
  "restrictions.clearSuccess":
    "Cleared the whitelist — access here now falls back to ordinary grants.",
  "restrictions.clearPartial":
    "Could not remove: {names} (at least one Admin entry must remain while others are whitelisted).",
  "restrictions.setFailed": "Failed to set restriction.",
  "restrictions.removeFailed": "Failed to remove restriction.",

  // Backend error codes (domain/errors.py + raise sites) — `errors.<code>`.
  // Generic per-status fallbacks come first; specific codes after.
  "errors.unauthorized": "Your session has expired. Please log in again.",
  "errors.forbidden": "You are not authorized to perform this action.",
  "errors.not_found": "The resource was not found. It may have been moved or deleted.",
  "errors.conflict": "This action conflicts with the resource's current state.",
  "errors.validation": "Some of the entered values are invalid.",
  "errors.invalid_child_type": "A {child} can't be placed inside a {parent}.",
  "errors.move_into_own_subtree": "A resource can't be moved into itself or one of its children.",
  "errors.move_requires_admin": "You need Admin access to the resource to move it.",
  "errors.move_destination_requires_editor":
    "You need Editor access or higher at the destination to move a resource there.",
  "errors.create_requires_editor": "You need Editor access or higher here to create inside it.",
  "errors.delete_requires_admin": "You need Admin access to delete this resource.",
  "errors.delete_not_empty": "Can't delete: {count} item(s) inside. Remove them first.",
  "errors.last_admin_restriction":
    "Can't remove the last Admin on the whitelist while other entries remain.",
} satisfies Record<string, string>;

export type MessageKey = keyof typeof en;
export type Messages = Record<MessageKey, string>;
