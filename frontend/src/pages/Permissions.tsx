import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { CatalogItem } from "../api/client";
import { getCatalog, isSuperEditor, UnauthorizedError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import CreateTeamWorkspaceModal from "../components/CreateTeamWorkspaceModal";
import LanguageToggle from "../components/LanguageToggle";
import ResourceNode from "../components/ResourceNode";
import { useLanguage } from "../i18n/LanguageContext";

const PAGE_SIZE = 20;
const SEARCH_DEBOUNCE_MS = 300;

export default function Permissions() {
  const { user, logout } = useAuth();
  const { t, tPlural, describeError } = useLanguage();
  const navigate = useNavigate();

  const [searchInput, setSearchInput] = useState("");
  const [query, setQuery] = useState("");

  const [items, setItems] = useState<CatalogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loadedPages, setLoadedPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false);

  // Debounce the search box into `query`.
  useEffect(() => {
    const handle = setTimeout(() => {
      setQuery(searchInput);
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [searchInput]);

  // Always (re)loads just the first page — used on initial load, on search
  // change, and after any modal action refetches the catalog. A prior
  // "Show all" expansion collapses back to the first page in that case,
  // same as this app's existing pattern elsewhere for post-change refetches.
  const loadCatalog = useCallback(() => {
    setIsLoading(true);
    setError(null);
    getCatalog({ search: query || undefined, page: 1, page_size: PAGE_SIZE })
      .then((response) => {
        setItems(response.items);
        setTotal(response.total);
        setLoadedPages(1);
      })
      .catch((err: unknown) => {
        if (err instanceof UnauthorizedError) {
          logout();
          navigate("/login", { replace: true });
          return;
        }
        setError(describeError(err, "permissions.loadFailed"));
      })
      .finally(() => {
        setIsLoading(false);
      });
    // describeError changes with the language; a language switch must not
    // refetch (and collapse) the catalog, so it's deliberately not a dep.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, logout, navigate]);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  // `total` is documented (CatalogService.get_catalog) as reflecting the
  // UNFILTERED universe — it includes other users' personal workspaces that
  // are hidden from this caller and will never actually appear on ANY page.
  // So looping until `accumulated.length >= total` can spin forever (found
  // via manual UI testing: it did, thousands of requests deep). The only
  // sound termination bound is the page COUNT implied by total/page_size —
  // some of those pages may legitimately come back with fewer items than
  // page_size, or even zero, once hidden items are filtered out.
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  // Kept separate from `isLoading`/loadCatalog's flag on purpose: flipping
  // the main isLoading flag would unmount the whole tree below (see the
  // "never gate the tree on isLoading alone" note near the render), closing
  // any modal a user has open in an already-visible ResourceNode while more
  // results stream in behind it.
  function handleShowAll() {
    setIsLoadingMore(true);
    setError(null);
    let accumulated = items;
    let nextPage = loadedPages + 1;

    function fetchNext(): Promise<void> {
      if (nextPage > totalPages) return Promise.resolve();
      return getCatalog({ search: query || undefined, page: nextPage, page_size: PAGE_SIZE }).then(
        (response) => {
          accumulated = [...accumulated, ...response.items];
          setItems(accumulated);
          setLoadedPages(nextPage);
          nextPage += 1;
          return fetchNext();
        },
      );
    }

    fetchNext()
      .catch((err: unknown) => {
        if (err instanceof UnauthorizedError) {
          logout();
          navigate("/login", { replace: true });
          return;
        }
        setError(describeError(err, "permissions.loadMoreFailed"));
      })
      .finally(() => setIsLoadingMore(false));
  }

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-4 px-4 py-4">
          <div>
            <h1 className="text-lg font-semibold text-slate-900">{t("permissions.title")}</h1>
            {user && (
              <p className="text-sm text-slate-500">
                <bdi>{user.name}</bdi> &middot; <bdi>{user.email}</bdi>
              </p>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <LanguageToggle />
            {isSuperEditor(user) && (
              <button
                type="button"
                onClick={() => setIsCreatingWorkspace(true)}
                className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
              >
                + {t("permissions.createTeamWorkspace")}
              </button>
            )}
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
            >
              {t("permissions.logout")}
            </button>
          </div>
        </div>
      </header>

      {isCreatingWorkspace && (
        <CreateTeamWorkspaceModal
          onClose={() => setIsCreatingWorkspace(false)}
          onCreated={loadCatalog}
        />
      )}

      <main className="mx-auto max-w-4xl px-4 py-6">
        <input
          type="search"
          placeholder={`${t("permissions.searchPlaceholder")}…`}
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none"
        />

        {error && (
          <p className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>
        )}

        {/* Only the very first load (no items yet) shows a full-page "Loading…" —
            a background refetch triggered by a modal action (grant/restriction/
            create) must NOT unmount the tree below, or any open modal inside a
            ResourceNode unmounts with it, discarding its just-shown success
            message. Found via manual UI testing 2026-07-31. */}
        {isLoading && items.length === 0 && (
          <p className="mt-6 text-sm text-slate-500">{`${t("common.loading")}…`}</p>
        )}

        {!isLoading && !error && items.length === 0 && (
          <p className="mt-6 text-sm text-slate-500">{t("permissions.noResults")}</p>
        )}

        {!error && items.length > 0 && (
          <div className="mt-4 space-y-3">
            {items.map((item) => (
              <ResourceNode key={item.id} item={item} depth={0} onChanged={loadCatalog} />
            ))}
          </div>
        )}

        {total > 0 && (
          <div className="mt-6 flex items-center justify-between">
            {/* Not "X of {total}" — `total` is the raw, unfiltered row count
                from the repo (see loadCatalog's comment above and
                CatalogService.get_catalog): it includes other users'
                personal workspaces that are permanently hidden from this
                caller and will never appear on any page, so it doesn't
                describe anything the user could actually reach by loading
                more. items.length is the only number that's ever true. */}
            <span className="text-sm text-slate-500">
              {tPlural("permissions.showing", items.length)}
            </span>
            {loadedPages < totalPages && (
              <button
                type="button"
                onClick={handleShowAll}
                disabled={isLoadingMore}
                className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isLoadingMore ? `${t("common.loading")}…` : t("permissions.showAll")}
              </button>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
