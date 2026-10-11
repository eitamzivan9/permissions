import type { GranteeType, MockUser, Team } from "../api/client";

/** Any row naming a grantee — a Grant, a Restriction, etc. */
export interface GranteeRef {
  grantee_type: GranteeType;
  user_id: string | null;
  team_id: string | null;
  locked?: boolean;
}

export interface ResolvedGrantee {
  /** Display name, or null if the id isn't in the directory. */
  name: string | null;
  /** The raw user/team id — the fallback label when `name` is null. */
  id: string;
  /** A user's email; null for teams. */
  email: string | null;
}

export function resolveGrantee(
  entry: GranteeRef,
  users: MockUser[],
  teams: Team[],
): ResolvedGrantee {
  if (entry.grantee_type === "user") {
    const user = users.find((candidate) => candidate.id === entry.user_id);
    return { name: user?.name ?? null, id: entry.user_id ?? "", email: user?.email ?? null };
  }
  const team = teams.find((candidate) => candidate.id === entry.team_id);
  return { name: team?.name ?? null, id: entry.team_id ?? "", email: null };
}

/** A stable list order, so a row doesn't jump after it's edited: locked
 * (workspace owner) rows first, then alphabetically by display name. */
export function sortGrantees<T extends GranteeRef>(
  entries: T[],
  users: MockUser[],
  teams: Team[],
): T[] {
  const label = (entry: T) => {
    const resolved = resolveGrantee(entry, users, teams);
    return resolved.name ?? resolved.id;
  };
  return [...entries].sort(
    (a, b) =>
      Number(Boolean(b.locked)) - Number(Boolean(a.locked)) ||
      label(a).localeCompare(label(b)),
  );
}
