import { useState } from "react";
import { useLanguage } from "../i18n/LanguageContext";

interface ConfirmButtonProps {
  label: string;
  onConfirm: () => void;
  disabled?: boolean;
}

// A small red text action that asks before it acts: the first click swaps
// it for inline Confirm / Cancel, so destructive row actions (Revoke,
// Remove, Clear all) all behave the same way.
export default function ConfirmButton({ label, onConfirm, disabled }: ConfirmButtonProps) {
  const { t } = useLanguage();
  const [isConfirming, setIsConfirming] = useState(false);

  if (!isConfirming) {
    return (
      <button
        type="button"
        onClick={() => setIsConfirming(true)}
        disabled={disabled}
        className="text-xs font-medium text-red-600 hover:text-red-800 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {label}
      </button>
    );
  }

  return (
    <span className="flex items-center gap-1.5">
      <button
        type="button"
        onClick={() => {
          setIsConfirming(false);
          onConfirm();
        }}
        disabled={disabled}
        className="rounded bg-red-600 px-1.5 py-0.5 text-xs font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {t("common.confirm")}
      </button>
      <button
        type="button"
        onClick={() => setIsConfirming(false)}
        className="text-xs font-medium text-slate-500 hover:text-slate-700"
      >
        {t("common.cancel")}
      </button>
    </span>
  );
}
