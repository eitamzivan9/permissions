import { useEffect, useState } from "react";
import type { GranteeType, MockUser, Restriction, Role, Team } from "../api/client";
import {
  deleteRestriction,
  getManageableUsers,
  getRestrictionsForResource,
  listTeams,
  setRestriction,
} from "../api/client";

interface RestrictionsModalProps {
  resourceId: string;
  resourceName: string;
  onClose: () => void;
  /** Called after a successful set/revoke so the caller can refetch the catalog. */
  onChanged: () => void;
}

const ROLE_OPTIONS: Role[] = ["viewer", "editor", "manager", "admin"];
const GRANTEE_TYPE_OPTIONS: GranteeType[] = ["user", "team"];

export default function RestrictionsModal({
  resourceId,
  resourceName,
  onClose,
  onChanged,
}: RestrictionsModalProps) {
  const [users, setUsers] = useState<MockUser[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [restrictions, setRestrictions] = useState<Restriction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [granteeType, setGranteeType] = useState<GranteeType>("user");
  const [selectedGranteeId, setSelectedGranteeId] = useState<string>("");
  const [selectedRole, setSelectedRole] = useState<Role>("viewer");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  function loadAll() {
    setIsLoading(true);
    setLoadError(null);
    Promise.all([
      getManageableUsers(resourceId),
      listTeams(),
      getRestrictionsForResource(resourceId),
    ])
      .then(([fetchedUsers, fetchedTeams, fetchedRestrictions]) => {
        setUsers(fetchedUsers);
        setTeams(fetchedTeams);
        setRestrictions(fetchedRestrictions);
        setSelectedGranteeId((current) => current || (fetchedUsers[0]?.id ?? ""));
      })
      .catch((error: unknown) => {
        setLoadError(error instanceof Error ? error.message : "Failed to load restrictions.");
      })
      .finally(() => setIsLoading(false));
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(loadAll, [resourceId]);

  const granteeOptions = granteeType === "user" ? users : teams;

  function handleGranteeTypeChange(next: GranteeType) {
    setGranteeType(next);
    const options = next === "user" ? users : teams;
    setSelectedGranteeId(options[0]?.id ?? "");
  }

  async function handleApply() {
    if (!selectedGranteeId) return;
    setIsSubmitting(true);
    setActionError(null);
    setSuccessMessage(null);
    try {
      await setRestriction({
        resourceId,
        granteeType,
        granteeId: selectedGranteeId,
        role: selectedRole,
      });
      setSuccessMessage(`Added ${selectedRole} to the whitelist.`);
      onChanged();
      loadAll();
    } catch (error: unknown) {
      setActionError(error instanceof Error ? error.message : "Failed to set restriction.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleRevoke(restriction: Restriction) {
    setIsSubmitting(true);
    setActionError(null);
    setSuccessMessage(null);
    try {
      await deleteRestriction({
        resourceId,
        granteeType: restriction.grantee_type,
        granteeId:
          (restriction.grantee_type === "user" ? restriction.user_id : restriction.team_id) ?? "",
      });
      setSuccessMessage("Removed from the whitelist.");
      onChanged();
      loadAll();
    } catch (error: unknown) {
      setActionError(error instanceof Error ? error.message : "Failed to remove restriction.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleClearAll() {
    setIsSubmitting(true);
    setActionError(null);
    setSuccessMessage(null);
    try {
      await Promise.all(
        restrictions.map((restriction) =>
          deleteRestriction({
            resourceId,
            granteeType: restriction.grantee_type,
            granteeId:
              (restriction.grantee_type === "user" ? restriction.user_id : restriction.team_id) ??
              "",
          }),
        ),
      );
      setSuccessMessage("Cleared the whitelist — access here now falls back to ordinary grants.");
      onChanged();
      loadAll();
    } catch (error: unknown) {
      setActionError(error instanceof Error ? error.message : "Failed to clear restrictions.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function granteeLabel(restriction: Restriction): string {
    if (restriction.grantee_type === "user") {
      const user = users.find((candidate) => candidate.id === restriction.user_id);
      return user ? `${user.name} (${user.email})` : (restriction.user_id ?? "unknown user");
    }
    const team = teams.find((candidate) => candidate.id === restriction.team_id);
    return team ? `Team: ${team.name}` : `Team: ${restriction.team_id ?? "unknown"}`;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-lg bg-white p-5 shadow-lg"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold text-slate-900">Restrictions (whitelist)</h3>
            <p className="mt-0.5 truncate text-sm text-slate-500">{resourceName}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-md px-2 py-1 text-sm text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <p className="mt-3 rounded-md bg-amber-50 p-2.5 text-xs text-amber-800">
          Adding anyone here turns this resource (and everything below it) into a whitelist:
          only grantees listed below keep access, even ones who currently have an Admin grant.
          This overrides ordinary access grants for everyone except a system Super Editor or
          Super Viewer.
        </p>

        {isLoading && <p className="mt-5 text-sm text-slate-500">Loading…</p>}
        {loadError && (
          <p className="mt-5 rounded-md bg-red-50 p-3 text-sm text-red-700">{loadError}</p>
        )}

        {!isLoading && !loadError && (
          <div className="mt-4 space-y-4">
            {restrictions.length > 0 && (
              <div>
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Currently whitelisted here
                  </h4>
                  <button
                    type="button"
                    onClick={handleClearAll}
                    disabled={isSubmitting}
                    className="text-xs font-medium text-red-600 hover:text-red-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Clear all
                  </button>
                </div>
                <ul className="mt-1.5 space-y-1.5">
                  {restrictions.map((restriction) => (
                    <li
                      key={`${restriction.grantee_type}:${restriction.user_id ?? restriction.team_id}`}
                      className="flex items-center justify-between gap-2 rounded-md bg-slate-50 px-2.5 py-1.5 text-sm"
                    >
                      <span className="truncate text-slate-700">{granteeLabel(restriction)}</span>
                      <span className="flex shrink-0 items-center gap-2">
                        <span className="capitalize text-slate-500">{restriction.role}</span>
                        <button
                          type="button"
                          onClick={() => handleRevoke(restriction)}
                          disabled={isSubmitting}
                          className="text-xs font-medium text-red-600 hover:text-red-800 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          Remove
                        </button>
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {restrictions.length === 0 && (
              <p className="text-sm text-slate-500">
                No whitelist here yet — access is governed by ordinary grants only.
              </p>
            )}

            <div className="border-t border-slate-200 pt-4">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Add to whitelist
              </h4>

              <div className="mt-2 flex gap-2">
                {GRANTEE_TYPE_OPTIONS.map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => handleGranteeTypeChange(option)}
                    className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                      granteeType === option
                        ? "bg-slate-900 text-white"
                        : "border border-slate-300 text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    {option === "user" ? "User" : "Team"}
                  </button>
                ))}
              </div>

              {granteeOptions.length === 0 ? (
                <p className="mt-3 text-sm text-slate-500">
                  {granteeType === "user" ? "No users available." : "No teams exist yet."}
                </p>
              ) : (
                <div className="mt-3 space-y-3">
                  <div>
                    <label
                      htmlFor="restrict-grantee"
                      className="block text-sm font-medium text-slate-700"
                    >
                      {granteeType === "user" ? "User" : "Team"}
                    </label>
                    <select
                      id="restrict-grantee"
                      className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none"
                      value={selectedGranteeId}
                      onChange={(event) => setSelectedGranteeId(event.target.value)}
                    >
                      {granteeType === "user"
                        ? users.map((user) => (
                            <option key={user.id} value={user.id}>
                              {user.name} ({user.email})
                            </option>
                          ))
                        : teams.map((team) => (
                            <option key={team.id} value={team.id}>
                              {team.name}
                            </option>
                          ))}
                    </select>
                  </div>

                  <div>
                    <label
                      htmlFor="restrict-role"
                      className="block text-sm font-medium text-slate-700"
                    >
                      Role
                    </label>
                    <select
                      id="restrict-role"
                      className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm capitalize text-slate-900 focus:border-slate-500 focus:outline-none"
                      value={selectedRole}
                      onChange={(event) => setSelectedRole(event.target.value as Role)}
                    >
                      {ROLE_OPTIONS.map((role) => (
                        <option key={role} value={role} className="capitalize">
                          {role}
                        </option>
                      ))}
                    </select>
                  </div>

                  <button
                    type="button"
                    onClick={handleApply}
                    disabled={isSubmitting || !selectedGranteeId}
                    className="w-full rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isSubmitting ? "Applying…" : "Add to whitelist"}
                  </button>
                </div>
              )}
            </div>

            {actionError && (
              <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{actionError}</p>
            )}
            {successMessage && (
              <p className="rounded-md bg-green-50 p-3 text-sm text-green-700">{successMessage}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
