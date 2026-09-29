import { useEffect, useState } from "react";
import type { Grant, GranteeType, MockUser, Restriction, Role, Team } from "../api/client";
import {
  deleteRestriction,
  getGrantsForResource,
  getManageableUsers,
  getRestrictionsForResource,
  listMockUsers,
  listTeams,
  setRestriction,
} from "../api/client";
import { useLanguage } from "../i18n/LanguageContext";
import { ROLE_LABEL_KEYS } from "../i18n/labels";

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
  const { t, describeError } = useLanguage();
  const [users, setUsers] = useState<MockUser[]>([]);
  // Full user directory, independent of `users` (which is scoped to whoever
  // the actor may manage/grant to). Grantee names must resolve regardless of
  // that scope — e.g. the actor's own auto-whitelisted entry, or another
  // admin's, is very often NOT a subordinate of the viewing actor.
  const [allUsers, setAllUsers] = useState<MockUser[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [restrictions, setRestrictions] = useState<Restriction[]>([]);
  // Ordinary (non-restriction) grants — used only to preview who already
  // holds Admin here before any restriction exists (see the "Admin today"
  // section below); RestrictionsService itself never reads these.
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
      getRestrictionsForResource(resourceId),
      getGrantsForResource(resourceId),
    ])
      .then(([fetchedUsers, fetchedAllUsers, fetchedTeams, fetchedRestrictions, fetchedGrants]) => {
        setUsers(fetchedUsers);
        setAllUsers(fetchedAllUsers);
        setTeams(fetchedTeams);
        setRestrictions(fetchedRestrictions);
        setGrants(fetchedGrants);
        setSelectedGranteeId((current) => current || (fetchedUsers[0]?.id ?? ""));
      })
      .catch((error: unknown) => {
        setLoadError(describeError(error, "restrictions.loadFailed"));
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
      setSuccessMessage(
        t("restrictions.addSuccess", { role: t(ROLE_LABEL_KEYS[selectedRole]) }),
      );
      onChanged();
      loadAll();
    } catch (error: unknown) {
      setActionError(describeError(error, "restrictions.setFailed"));
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
      setSuccessMessage(t("restrictions.removeSuccess"));
      onChanged();
      loadAll();
    } catch (error: unknown) {
      setActionError(describeError(error, "restrictions.removeFailed"));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleClearAll() {
    setIsSubmitting(true);
    setActionError(null);
    setSuccessMessage(null);
    // Sequential, not Promise.all: the backend blocks removing the last
    // Admin-role entry while other entries remain, so entries must be
    // removed one at a time (parallel deletes could each pass a stale
    // "another admin remains" check before either commits). This also lets
    // us report exactly which entries couldn't be cleared instead of
    // failing the whole batch on the first rejection.
    const failures: string[] = [];
    for (const restriction of restrictions) {
      try {
        await deleteRestriction({
          resourceId,
          granteeType: restriction.grantee_type,
          granteeId:
            (restriction.grantee_type === "user" ? restriction.user_id : restriction.team_id) ??
            "",
        });
      } catch {
        failures.push(granteeLabel(restriction));
      }
    }
    if (failures.length > 0) {
      setActionError(t("restrictions.clearPartial", { names: failures.join(", ") }));
    } else {
      setSuccessMessage(t("restrictions.clearSuccess"));
    }
    onChanged();
    loadAll();
    setIsSubmitting(false);
  }

  function granteeLabel(entry: Restriction | Grant): string {
    if (entry.grantee_type === "user") {
      const user = allUsers.find((candidate) => candidate.id === entry.user_id);
      return user
        ? t("common.userOption", { name: user.name, email: user.email })
        : (entry.user_id ?? t("common.unknownUser"));
    }
    const team = teams.find((candidate) => candidate.id === entry.team_id);
    return t("common.teamLabel", {
      name: team ? team.name : (entry.team_id ?? t("common.unknown")),
    });
  }

  // Admins here today via an ordinary grant — shown only until the first
  // restriction is set, since RestrictionService.set_restriction() then
  // auto-whitelists whoever sets it (not necessarily every admin listed
  // here) and this list would start drifting from the real whitelist.
  const currentAdminGrants = grants.filter((grant) => grant.role === "admin");

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
            <h3 className="text-base font-semibold text-slate-900">{t("restrictions.title")}</h3>
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

        <p className="mt-3 rounded-md bg-amber-50 p-2.5 text-xs text-amber-800">
          {t("restrictions.warning")}
        </p>

        {isLoading && <p className="mt-5 text-sm text-slate-500">{`${t("common.loading")}…`}</p>}
        {loadError && (
          <p className="mt-5 rounded-md bg-red-50 p-3 text-sm text-red-700">{loadError}</p>
        )}

        {!isLoading && !loadError && (
          <div className="mt-4 space-y-4">
            {restrictions.length > 0 && (
              <div>
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    {t("restrictions.current")}
                  </h4>
                  <button
                    type="button"
                    onClick={handleClearAll}
                    disabled={isSubmitting}
                    className="text-xs font-medium text-red-600 hover:text-red-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {t("restrictions.clearAll")}
                  </button>
                </div>
                <ul className="mt-1.5 space-y-1.5">
                  {restrictions.map((restriction) => (
                    <li
                      key={`${restriction.grantee_type}:${restriction.user_id ?? restriction.team_id}`}
                      className="flex items-center justify-between gap-2 rounded-md bg-slate-50 px-2.5 py-1.5 text-sm"
                    >
                      <span className="truncate text-slate-700" dir="auto">
                        {granteeLabel(restriction)}
                      </span>
                      <span className="flex shrink-0 items-center gap-2">
                        <span className="text-slate-500">{t(ROLE_LABEL_KEYS[restriction.role])}</span>
                        <button
                          type="button"
                          onClick={() => handleRevoke(restriction)}
                          disabled={isSubmitting}
                          className="text-xs font-medium text-red-600 hover:text-red-800 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {t("restrictions.remove")}
                        </button>
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {restrictions.length === 0 && (
              <div>
                <p className="text-sm text-slate-500">
                  {t("restrictions.none")}
                </p>
                {currentAdminGrants.length > 0 && (
                  <div className="mt-2">
                    <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      {t("restrictions.adminToday")}
                    </h4>
                    <ul className="mt-1.5 space-y-1.5">
                      {currentAdminGrants.map((grant) => (
                        <li
                          key={`${grant.grantee_type}:${grant.user_id ?? grant.team_id}`}
                          className="flex items-center justify-between gap-2 rounded-md bg-slate-50 px-2.5 py-1.5 text-sm"
                        >
                          <span className="truncate text-slate-700" dir="auto">
                            {granteeLabel(grant)}
                          </span>
                          <span className="text-slate-500">{t("role.admin")}</span>
                        </li>
                      ))}
                    </ul>
                    <p className="mt-1 text-xs text-slate-400">
                      {t("restrictions.adminTodayHint")}
                    </p>
                  </div>
                )}
              </div>
            )}

            <div className="border-t border-slate-200 pt-4">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {t("restrictions.add")}
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
                  {granteeType === "user" ? t("restrictions.noUsers") : t("common.noTeams")}
                </p>
              ) : (
                <div className="mt-3 space-y-3">
                  <div>
                    <label
                      htmlFor="restrict-grantee"
                      className="block text-sm font-medium text-slate-700"
                    >
                      {granteeType === "user" ? t("common.user") : t("common.team")}
                    </label>
                    <select
                      id="restrict-grantee"
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
                    <label
                      htmlFor="restrict-role"
                      className="block text-sm font-medium text-slate-700"
                    >
                      {t("common.role")}
                    </label>
                    <select
                      id="restrict-role"
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
                    {isSubmitting ? `${t("common.applying")}…` : t("restrictions.add")}
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
