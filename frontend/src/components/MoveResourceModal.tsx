import { useEffect, useState } from "react";
import type { CatalogItem, ResourceType } from "../api/client";
import { getCatalog, moveResource } from "../api/client";

interface MoveResourceModalProps {
  resourceId: string;
  resourceName: string;
  onClose: () => void;
  /** Called after a successful move so the caller can refetch the catalog. */
  onChanged: () => void;
}

const TYPE_LABELS: Record<ResourceType, string> = {
  workspace: "Workspace",
  folder: "Folder",
  map: "Map",
  group: "Group",
  layer: "Layer",
};

const SEARCH_DEBOUNCE_MS = 300;
const SEARCH_PAGE_SIZE = 10;

// Flattens a catalog page's tree into a single list of candidate
// destinations — search already returns each match with its full subtree,
// but a destination picker just needs "does this look like the place I
// mean," not the nested structure.
function flatten(items: CatalogItem[]): CatalogItem[] {
  const result: CatalogItem[] = [];
  for (const item of items) {
    result.push(item);
    result.push(...flatten(item.children));
  }
  return result;
}

export default function MoveResourceModal({
  resourceId,
  resourceName,
  onClose,
  onChanged,
}: MoveResourceModalProps) {
  const [searchInput, setSearchInput] = useState("");
  const [results, setResults] = useState<CatalogItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => {
      const q = searchInput.trim();
      if (!q) {
        setResults([]);
        return;
      }
      setIsSearching(true);
      getCatalog({ q, page: 1, page_size: SEARCH_PAGE_SIZE })
        .then((response) => {
          // A resource can't become its own parent — filter it out client
          // side too (the backend also rejects moving into your own subtree).
          setResults(flatten(response.items).filter((item) => item.id !== resourceId));
        })
        .catch(() => setResults([]))
        .finally(() => setIsSearching(false));
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [searchInput, resourceId]);

  async function handleMove() {
    if (!selectedId) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await moveResource({ resourceId, newParentId: selectedId });
      onChanged();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to move the resource.");
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
            <h3 className="text-base font-semibold text-slate-900">Move resource</h3>
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

        <div className="mt-4 space-y-3">
          <div>
            <label htmlFor="move-destination-search" className="block text-sm font-medium text-slate-700">
              New parent
            </label>
            <input
              id="move-destination-search"
              type="search"
              value={searchInput}
              onChange={(event) => {
                setSearchInput(event.target.value);
                setSelectedId(null);
              }}
              placeholder="Search by name…"
              className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none"
            />
          </div>

          {isSearching && <p className="text-sm text-slate-500">Searching…</p>}

          {!isSearching && searchInput.trim() && results.length === 0 && (
            <p className="text-sm text-slate-500">No matches.</p>
          )}

          {results.length > 0 && (
            <ul className="max-h-56 space-y-1 overflow-y-auto">
              {results.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedId(item.id)}
                    className={`flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-left text-sm ${
                      selectedId === item.id
                        ? "bg-slate-900 text-white"
                        : "bg-slate-50 text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    <span
                      className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide ${
                        selectedId === item.id ? "bg-white/20" : "bg-slate-200 text-slate-500"
                      }`}
                    >
                      {TYPE_LABELS[item.type]}
                    </span>
                    <span className="truncate">{item.name}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}

          <button
            type="button"
            onClick={handleMove}
            disabled={isSubmitting || !selectedId}
            className="w-full rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isSubmitting ? "Moving…" : "Move here"}
          </button>

          {error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        </div>
      </div>
    </div>
  );
}
