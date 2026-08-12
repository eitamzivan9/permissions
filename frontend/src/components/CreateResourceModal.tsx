import { useState } from "react";
import type { ResourceType } from "../api/client";
import { createResource } from "../api/client";

interface CreateResourceModalProps {
  parentId: string;
  parentName: string;
  onClose: () => void;
  /** Called after a successful create so the caller can refetch the catalog. */
  onCreated: () => void;
}

// Map/Layer are never frontend-creatable — this permissions server doesn't
// own that data, creation is meant to happen server-to-server. Only these
// two purely-organizational types are offered here.
const TYPE_OPTIONS: { value: ResourceType; label: string }[] = [
  { value: "folder", label: "Folder" },
  { value: "group", label: "Group" },
];

export default function CreateResourceModal({
  parentId,
  parentName,
  onClose,
  onCreated,
}: CreateResourceModalProps) {
  const [type, setType] = useState<ResourceType>("folder");
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate() {
    if (!name.trim()) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await createResource({ type, name: name.trim(), parentId });
      onCreated();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create the resource.");
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
            <h3 className="text-base font-semibold text-slate-900">Create resource</h3>
            <p className="mt-0.5 truncate text-sm text-slate-500">Inside {parentName}</p>
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

        <div className="mt-5 space-y-3">
          <div>
            <label htmlFor="create-resource-type" className="block text-sm font-medium text-slate-700">
              Type
            </label>
            <select
              id="create-resource-type"
              className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none"
              value={type}
              onChange={(event) => setType(event.target.value as ResourceType)}
            >
              {TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="create-resource-name" className="block text-sm font-medium text-slate-700">
              Name
            </label>
            <input
              id="create-resource-name"
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none"
              placeholder="e.g. Zoning Districts"
            />
          </div>

          <button
            type="button"
            onClick={handleCreate}
            disabled={isSubmitting || !name.trim()}
            className="w-full rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isSubmitting ? "Creating…" : "Create"}
          </button>

          {error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        </div>
      </div>
    </div>
  );
}
