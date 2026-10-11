import type { MockUser, Team } from "../api/client";
import { useLanguage } from "../i18n/LanguageContext";
import type { GranteeRef } from "../lib/grantees";
import { resolveGrantee } from "../lib/grantees";

interface GranteeNameProps {
  entry: GranteeRef;
  users: MockUser[];
  teams: Team[];
}

// Name on top, email (or "Team") underneath — so a long email never cuts
// the name itself off. Shared by the grant and whitelist rows.
export default function GranteeName({ entry, users, teams }: GranteeNameProps) {
  const { t } = useLanguage();
  const { name, id, email } = resolveGrantee(entry, users, teams);
  const fallback = entry.grantee_type === "user" ? t("common.unknownUser") : t("common.unknown");
  return (
    <span className="min-w-0">
      <span className="block truncate font-medium text-slate-800">
        <bdi>{name ?? (id || fallback)}</bdi>
      </span>
      <span className="block truncate text-xs text-slate-500">
        {entry.grantee_type === "user" ? <bdi>{email ?? id}</bdi> : t("common.team")}
      </span>
    </span>
  );
}
