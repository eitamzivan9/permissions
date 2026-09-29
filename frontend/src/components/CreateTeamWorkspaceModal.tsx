import { useEffect, useState } from "react";
import type { MockUser } from "../api/client";
import { createTeamWorkspace, listMockUsers } from "../api/client";
import { useLanguage } from "../i18n/LanguageContext";

interface CreateTeamWorkspaceModalProps {
  onClose: () => void;
  /** Called after a successful create so the caller can refetch the catalog. */
  onCreated: () => void;
}

export default function CreateTeamWorkspaceModal({
  onClose,
  onCreated,
}: CreateTeamWorkspaceModalProps) {
  const { t, describeError } = useLanguage();
  const [users, setUsers] = useState<MockUser[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [adminUserId, setAdminUserId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listMockUsers()
      .then((fetchedUsers) => {
        setUsers(fetchedUsers);
        setAdminUserId((current) => current || (fetchedUsers[0]?.id ?? ""));
      })
      .catch((err: unknown) => {
        setLoadError(describeError(err, "teamWorkspace.loadUsersFailed"));
      })
      .finally(() => setIsLoadingUsers(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleCreate() {
    if (!name.trim() || !adminUserId) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await createTeamWorkspace({ name: name.trim(), adminUserId });
      onCreated();
      onClose();
    } catch (err: unknown) {
      setError(describeError(err, "teamWorkspace.failed"));
    } finally {
      setIsSubmitting(false);
    }
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
            <h3 className="text-base font-semibold text-slate-900">{t("teamWorkspace.title")}</h3>
            <p className="mt-0.5 text-sm text-slate-500">{t("teamWorkspace.subtitle")}</p>
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

        {isLoadingUsers && <p className="mt-5 text-sm text-slate-500">{`${t("common.loading")}…`}</p>}
        {loadError && (
          <p className="mt-5 rounded-md bg-red-50 p-3 text-sm text-red-700">{loadError}</p>
        )}

        {!isLoadingUsers && !loadError && (
          <div className="mt-5 space-y-3">
            <div>
              <label htmlFor="team-ws-name" className="block text-sm font-medium text-slate-700">
                {t("common.name")}
              </label>
              <input
                id="team-ws-name"
                type="text"
                value={name}
                onChange={(event) => setName(event.target.value)}
                // Empty: follow the page direction so the placeholder aligns with it;
                // typed: let the browser pick the direction from the name itself.
                dir={name ? "auto" : undefined}
                className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none"
                placeholder={t("teamWorkspace.placeholder")}
              />
            </div>

            <div>
              <label htmlFor="team-ws-admin" className="block text-sm font-medium text-slate-700">
                {t("teamWorkspace.initialAdmin")}
              </label>
              <select
                id="team-ws-admin"
                className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none"
                value={adminUserId}
                onChange={(event) => setAdminUserId(event.target.value)}
              >
                {users.map((user) => (
                  <option key={user.id} value={user.id} dir="auto">
                    {t("common.userOption", { name: user.name, email: user.email })}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="button"
              onClick={handleCreate}
              disabled={isSubmitting || !name.trim() || !adminUserId}
              className="w-full rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSubmitting ? `${t("common.creating")}…` : t("common.create")}
            </button>

            {error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          </div>
        )}
      </div>
    </div>
  );
}
