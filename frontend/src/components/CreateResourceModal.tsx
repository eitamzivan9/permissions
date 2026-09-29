import { useState } from "react";
import { createResource } from "../api/client";
import { useLanguage } from "../i18n/LanguageContext";

interface CreateResourceModalProps {
  parentId: string;
  parentName: string;
  onClose: () => void;
  /** Called after a successful create so the caller can refetch the catalog. */
  onCreated: () => void;
}

// Map/Layer/Group are never frontend-creatable — this permissions server
// doesn't own that data (Map/Layer), and Group creation is backend-only by
// deliberate choice (confirmed with the project owner). Only Folder is
// offered here, so there's no type picker at all — POST /resources itself
// still accepts any ResourceType for server-to-server/manual calls.
export default function CreateResourceModal({
  parentId,
  parentName,
  onClose,
  onCreated,
}: CreateResourceModalProps) {
  const { t, describeError } = useLanguage();
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate() {
    if (!name.trim()) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await createResource({ type: "folder", name: name.trim(), parentId });
      onCreated();
      onClose();
    } catch (err: unknown) {
      setError(describeError(err, "createResource.failed"));
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
            <h3 className="text-base font-semibold text-slate-900">{t("createResource.title")}</h3>
            <p className="mt-0.5 truncate text-sm text-slate-500">
              {t("createResource.inside")}{" "}
              <bdi>{parentName}</bdi>
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

        <div className="mt-5 space-y-3">
          <div>
            <label htmlFor="create-resource-name" className="block text-sm font-medium text-slate-700">
              {t("common.name")}
            </label>
            <input
              id="create-resource-name"
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              // Empty: follow the page direction so the placeholder aligns with it;
              // typed: let the browser pick the direction from the name itself.
              dir={name ? "auto" : undefined}
              className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none"
              placeholder={t("createResource.placeholder")}
            />
          </div>

          <button
            type="button"
            onClick={handleCreate}
            disabled={isSubmitting || !name.trim()}
            className="w-full rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isSubmitting ? `${t("common.creating")}…` : t("common.create")}
          </button>

          {error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        </div>
      </div>
    </div>
  );
}
