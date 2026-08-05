import { useEffect, useState } from "react";
import type { Grant, GranteeType, MockUser, Role, Team } from "../api/client";
import {
  deleteGrant,
  getGrantsForResource,
  getManageableUsers,
  listTeams,
  setGrant,
} from "../api/client";

interface ManageAccessModalProps {
  resourceId: string;
  resourceName: string;
  onClose: () => void;
  /** Called after a successful grant/revoke so the caller can refetch the catalog. */
  onChanged: () => void;
}

const ROLE_OPTIONS: Role[] = ["viewer", "editor", "manager", "admin"];
const GRANTEE_TYPE_OPTIONS: GranteeType[] = ["user", "team"];

export default function ManageAccessModal({
  resourceId,
  resourceName,
  onClose,
  onChanged,
}: ManageAccessModalProps) {
  const [users, setUsers] = useState<MockUser[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [grants, setGrants] = useState<Grant[]>([]);
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
    Promise.all([getManageableUsers(resourceId), listTeams(), getGrantsForResource(resourceId)])
      .then(([fetchedUsers, fetchedTeams, fetchedGrants]) => {
        setUsers(fetchedUsers);
        setTeams(fetchedTeams);
        setGrants(fetchedGrants);
        setSelectedGranteeId((current) => current || (fetchedUsers[0]?.id ?? ""));
      })
      .catch((error: unknown) => {
        setLoadError(error instanceof Error ? error.message : "Failed to load access data.");
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
      await setGrant({ resourceId, granteeType, granteeId: selectedGranteeId, role: selectedRole });
      setSuccessMessage(`Set ${selectedRole} access.`);
      onChanged();
      loadAll();
    } catch (error: unknown) {
      setActionError(error instanceof Error ? error.message : "Failed to update access.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleRevoke(grant: Grant) {
    setIsSubmitting(true);
    setActionError(null);
    setSuccessMessage(null);
    try {
      await deleteGrant({
        resourceId,
        granteeType: grant.grantee_type,
        granteeId: (grant.grantee_type === "user" ? grant.user_id : grant.team_id) ?? "",
      });
      setSuccessMessage("Grant revoked.");
      onChanged();
      loadAll();
    } catch (error: unknown) {
      setActionError(error instanceof Error ? error.message : "Failed to revoke access.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function granteeLabel(grant: Grant): string {
    if (grant.grantee_type === "user") {
      const user = users.find((candidate) => candidate.id === grant.user_id);
      return user ? `${user.name} (${user.email})` : (grant.user_id ?? "unknown user");
    }
    const team = teams.find((candidate) => candidate.id === grant.team_id);
    return team ? `Team: ${team.name}` : `Team: ${grant.team_id ?? "unknown"}`;
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
            <h3 className="text-base font-semibold text-slate-900">Manage access</h3>
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

        {isLoading && <p className="mt-5 text-sm text-slate-500">Loading…</p>}
        {loadError && (
          <p className="mt-5 rounded-md bg-red-50 p-3 text-sm text-red-700">{loadError}</p>
        )}

        {!isLoading && !loadError && (
          <div className="mt-5 space-y-4">
            {grants.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Current grants here
                </h4>
                <ul className="mt-1.5 space-y-1.5">
                  {grants.map((grant) => (
                    <li
                      key={`${grant.grantee_type}:${grant.user_id ?? grant.team_id}`}
                      className="flex items-center justify-between gap-2 rounded-md bg-slate-50 px-2.5 py-1.5 text-sm"
                    >
                      <span className="truncate text-slate-700">{granteeLabel(grant)}</span>
                      <span className="flex shrink-0 items-center gap-2">
                        <span className="capitalize text-slate-500">{grant.role}</span>
                        <button
                          type="button"
                          onClick={() => handleRevoke(grant)}
                          disabled={isSubmitting}
                          className="text-xs font-medium text-red-600 hover:text-red-800 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          Revoke
                        </button>
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="border-t border-slate-200 pt-4">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Grant access
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
                  {granteeType === "user"
                    ? "You have no subordinates to grant access to."
                    : "No teams exist yet."}
                </p>
              ) : (
                <div className="mt-3 space-y-3">
                  <div>
                    <label
                      htmlFor="manage-grantee"
                      className="block text-sm font-medium text-slate-700"
                    >
                      {granteeType === "user" ? "User" : "Team"}
                    </label>
                    <select
                      id="manage-grantee"
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
                    <label htmlFor="manage-role" className="block text-sm font-medium text-slate-700">
                      Role
                    </label>
                    <select
                      id="manage-role"
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
                    {isSubmitting ? "Applying…" : "Grant access"}
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
