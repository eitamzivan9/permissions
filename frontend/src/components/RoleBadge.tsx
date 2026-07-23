import type { Role } from "../api/client";

// Shared visual mapping for effective roles so ResourceNode (and any future
// consumer) doesn't reinvent the color scheme. `null` means no role at all,
// including one that could bubble up from nowhere (see can_fetch on ResourceNode).
const ROLE_STYLES: Record<Role, string> = {
  viewer: "bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-300",
  editor: "bg-green-50 text-green-700 ring-1 ring-inset ring-green-300",
  manager: "bg-purple-50 text-purple-700 ring-1 ring-inset ring-purple-300",
  admin: "bg-amber-50 text-amber-800 ring-1 ring-inset ring-amber-300",
};
const NO_ROLE_STYLE = "bg-slate-100 text-slate-500 ring-1 ring-inset ring-slate-300";

interface RoleBadgeProps {
  role: Role | null;
}

export default function RoleBadge({ role }: RoleBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize ${
        role ? ROLE_STYLES[role] : NO_ROLE_STYLE
      }`}
    >
      {role ?? "no access"}
    </span>
  );
}
