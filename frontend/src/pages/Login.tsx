import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { listMockUsers } from "../api/client";
import type { MockUser } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import LanguageToggle from "../components/LanguageToggle";
import { useLanguage } from "../i18n/LanguageContext";

export default function Login() {
  const [users, setUsers] = useState<MockUser[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedUserId, setSelectedUserId] = useState<string>("");
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [signInError, setSignInError] = useState<string | null>(null);

  const { login, isAuthenticated } = useAuth();
  const { t, describeError } = useLanguage();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    let cancelled = false;
    listMockUsers()
      .then((fetched) => {
        if (cancelled) return;
        setUsers(fetched);
        if (fetched.length > 0) {
          setSelectedUserId(fetched[0].id);
        }
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setLoadError(describeError(error, "login.loadUsersFailed"));
      })
      .finally(() => {
        if (!cancelled) setIsLoadingUsers(false);
      });
    return () => {
      cancelled = true;
    };
    // describeError is recreated per language; re-fetching on a language
    // switch isn't wanted, so it's deliberately left out of the deps.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!selectedUserId) return;
    setIsSigningIn(true);
    setSignInError(null);
    try {
      await login(selectedUserId);
      navigate("/", { replace: true });
    } catch (error: unknown) {
      setSignInError(describeError(error, "login.failed"));
    } finally {
      setIsSigningIn(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="absolute end-4 top-4">
        <LanguageToggle />
      </div>
      <div className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-semibold text-slate-900">{t("login.title")}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {t("login.subtitle")}
        </p>

        {isLoadingUsers && (
          <p className="mt-6 text-sm text-slate-500">{`${t("login.loadingUsers")}…`}</p>
        )}

        {loadError && (
          <p className="mt-6 rounded-md bg-red-50 p-3 text-sm text-red-700">{loadError}</p>
        )}

        {!isLoadingUsers && !loadError && (
          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="mock-user" className="block text-sm font-medium text-slate-700">
                {t("login.signInAs")}
              </label>
              <select
                id="mock-user"
                className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none"
                value={selectedUserId}
                onChange={(event) => setSelectedUserId(event.target.value)}
              >
                {users.map((user) => (
                  <option key={user.id} value={user.id} dir="auto">
                    {t("common.userOption", { name: user.name, email: user.email })}
                  </option>
                ))}
              </select>
            </div>

            {signInError && (
              <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{signInError}</p>
            )}

            <button
              type="submit"
              disabled={!selectedUserId || isSigningIn}
              className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSigningIn ? `${t("login.signingIn")}…` : t("login.signIn")}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
