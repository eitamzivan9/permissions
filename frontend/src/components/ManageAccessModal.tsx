import { useEffect, useState } from "react";
import type { Grant, GranteeType, MockUser, Role, Team } from "../api/client";
import {
  deleteGrant,
  getGrantsForResource,
  getManageableUsers,
  listMockUsers,
  listTeams,
  setGrant,
} from "../api/client";
import { useLanguage } from "../i18n/LanguageContext";
import { ROLE_LABEL_KEYS } from "../i18n/labels";

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
  const { t, describeError } = useLanguage();
  const [users, setUsers] = useState<MockUser[]>([]);
  // Full user directory, independent of `users` (scoped to who the actor may
  // grant to) — an existing grantee's name must resolve regardless, e.g. the
  // actor's own grant, same as RestrictionsModal.
  const [allUsers, setAllUsers] = useState<MockUser[]>([]);
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
    Promise.all([
      getManageableUsers(resourceId),
      listMockUsers(),
      listTeams(),
      getGrantsForResource(resourceId),
    ])
      .then(([fetchedUsers, fetchedAllUsers, fetchedTeams, fetchedGrants]) => {
        setUsers(fetchedUsers);
        setAllUsers(fetchedAllUsers);
        setTeams(fetchedTeams);
        setGrants(fetchedGrants);
        setSelectedGranteeId((current) => current || (fetchedUsers[0]?.id ?? ""));
      })
      .catch((error: unknown) => {
        setLoadError(describeError(error, "manageAccess.loadFailed"));
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
      setSuccessMessage(
        t("manageAccess.setSuccess", { role: t(ROLE_LABEL_KEYS[selectedRole]) }),
      );
      onChanged();
      loadAll();
    } catch (error: unknown) {
      setActionError(describeError(error, "manageAccess.updateFailed"));
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
      setSuccessMessage(t("manageAccess.revokeSuccess"));
      onChanged();
      loadAll();
    } catch (error: unknown) {
      setActionError(describeError(error, "manageAccess.revokeFailed"));
    } finally {
      setIsSubmitting(false);
    }
  }

  function granteeLabel(grant: Grant): string {
    if (grant.grantee_type === "user") {
      const user = allUsers.find((candidate) => candidate.id === grant.user_id);
      return user
        ? t("common.userOption", { name: user.name, email: user.email })
        : (grant.user_id ?? t("common.unknownUser"));
    }
    const team = teams.find((candidate) => candidate.id === grant.team_id);
    return t("common.teamLabel", {
      name: team ? team.name : (grant.team_id ?? t("common.unknown")),
    });
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
            <h3 className="text-base font-semibold text-slate-900">{t("manageAccess.title")}</h3>
            <p className="mt-0.5 truncate text-sm text-slate-500">
              <bdi>{resourceName}</bdi>
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-md px-2 py-1 text-sm text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label={t("common.close")}
          >
            ✕
          </button>
        </div>

        {isLoading && <p className="mt-5 text-sm text-slate-500">{`${t("common.loading")}…`}</p>}
        {loadError && (
          <p className="mt-5 rounded-md bg-red-50 p-3 text-sm text-red-700">{loadError}</p>
        )}

        {!isLoading && !loadError && (
          <div className="mt-5 space-y-4">
            {grants.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  {t("manageAccess.currentGrants")}
                </h4>
                <ul className="mt-1.5 space-y-1.5">
                  {grants.map((grant) => (
                    <li
                      key={`${grant.grantee_type}:${grant.user_id ?? grant.team_id}`}
                      className="flex items-center justify-between gap-2 rounded-md bg-slate-50 px-2.5 py-1.5 text-sm"
                    >
                      <span className="truncate text-slate-700" dir="auto">
                        {granteeLabel(grant)}
                      </span>
                      <span className="flex shrink-0 items-center gap-2">
                        <span className="text-slate-500">{t(ROLE_LABEL_KEYS[grant.role])}</span>
                        <button
                          type="button"
                          onClick={() => handleRevoke(grant)}
                          disabled={isSubmitting}
                          className="text-xs font-medium text-red-600 hover:text-red-800 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {t("manageAccess.revoke")}
                        </button>
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="border-t border-slate-200 pt-4">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {t("manageAccess.grantAccess")}
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
                    {option === "user" ? t("common.user") : t("common.team")}
                  </button>
                ))}
              </div>

              {granteeOptions.length === 0 ? (
                <p className="mt-3 text-sm text-slate-500">
                  {granteeType === "user"
                    ? t("manageAccess.noSubordinates")
                    : t("common.noTeams")}
                </p>
              ) : (
                <div className="mt-3 space-y-3">
                  <div>
                    <label
                      htmlFor="manage-grantee"
                      className="block text-sm font-medium text-slate-700"
                    >
                      {granteeType === "user" ? t("common.user") : t("common.team")}
                    </label>
                    <select
                      id="manage-grantee"
                      className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none"
                      value={selectedGranteeId}
                      onChange={(event) => setSelectedGranteeId(event.target.value)}
                    >
                      {granteeType === "user"
                        ? users.map((user) => (
                            <option key={user.id} value={user.id} dir="auto">
                              {t("common.userOption", { name: user.name, email: user.email })}
                            </option>
                          ))
                        : teams.map((team) => (
                            <option key={team.id} value={team.id} dir="auto">
                              {team.name}
                            </option>
                          ))}
                    </select>
                  </div>

                  <div>
                    <label htmlFor="manage-role" className="block text-sm font-medium text-slate-700">
                      {t("common.role")}
                    </label>
                    <select
                      id="manage-role"
                      className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none"
                      value={selectedRole}
                      onChange={(event) => setSelectedRole(event.target.value as Role)}
                    >
                      {ROLE_OPTIONS.map((role) => (
                        <option key={role} value={role}>
                          {t(ROLE_LABEL_KEYS[role])}
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
                    {isSubmitting ? `${t("common.applying")}…` : t("manageAccess.grantAccess")}
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
