import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { CatalogItem } from "../api/client";
import { getCatalog, isSuperEditor, UnauthorizedError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import CreateTeamWorkspaceModal from "../components/CreateTeamWorkspaceModal";
import ResourceNode from "../components/ResourceNode";

const PAGE_SIZE = 4;
const SEARCH_DEBOUNCE_MS = 300;

export default function Permissions() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [searchInput, setSearchInput] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);

  const [items, setItems] = useState<CatalogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false);

  // Debounce the search box into `query`, resetting to page 1 on change.
  useEffect(() => {
    const handle = setTimeout(() => {
      setQuery(searchInput);
      setPage(1);
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [searchInput]);

  const loadCatalog = useCallback(() => {
    setIsLoading(true);
    setError(null);
    getCatalog({ q: query || undefined, page, page_size: PAGE_SIZE })
      .then((response) => {
        setItems(response.items);
        setTotal(response.total);
      })
      .catch((err: unknown) => {
        if (err instanceof UnauthorizedError) {
          logout();
          navigate("/login", { replace: true });
          return;
        }
        setError(err instanceof Error ? err.message : "Failed to load the catalog.");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [query, page, logout, navigate]);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-4 px-4 py-4">
          <div>
            <h1 className="text-lg font-semibold text-slate-900">Resource Access</h1>
            {user && (
              <p className="text-sm text-slate-500">
                {user.name} &middot; {user.email}
              </p>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {isSuperEditor(user) && (
              <button
                type="button"
                onClick={() => setIsCreatingWorkspace(true)}
                className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
              >
                + Create team workspace
              </button>
            )}
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
            >
              Log out
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
          placeholder="Search by name (any workspace, folder, map, group, or layer)…"
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
          <p className="mt-6 text-sm text-slate-500">Loading…</p>
        )}

        {!isLoading && !error && items.length === 0 && (
          <p className="mt-6 text-sm text-slate-500">Nothing matches your search.</p>
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
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1 || isLoading}
              className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-sm text-slate-500">
              Page {page} of {totalPages} &middot; {total} results
            </span>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || isLoading}
              className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
