import type { Role } from "../api/client";
import { useLanguage } from "../i18n/LanguageContext";
import { ROLE_LABEL_KEYS } from "../i18n/labels";

const ROLE_OPTIONS: Role[] = ["viewer", "editor", "manager", "admin"];

interface RoleSelectProps {
  role: Role;
  /** Called only when a DIFFERENT role is picked. */
  onChange: (role: Role) => void;
  disabled?: boolean;
  title?: string;
}

// Compact inline role picker for an existing grant/whitelist row — shared by
// ManageAccessModal and RestrictionsModal so both rows look and behave the
// same. Bound to `role`, so a change the server rejects snaps back on its own
// once the caller's list reloads unchanged.
export default function RoleSelect({ role, onChange, disabled, title }: RoleSelectProps) {
  const { t } = useLanguage();
  return (
    <select
      aria-label={t("common.role")}
      title={title}
      value={role}
      disabled={disabled}
      onChange={(event) => {
        const next = event.target.value as Role;
        if (next !== role) onChange(next);
      }}
      className="rounded-md border border-slate-300 bg-white py-0.5 ps-2 pe-1 text-xs text-slate-900 focus:border-slate-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
    >
      {ROLE_OPTIONS.map((option) => (
        <option key={option} value={option}>
          {t(ROLE_LABEL_KEYS[option])}
        </option>
      ))}
    </select>
  );
}
