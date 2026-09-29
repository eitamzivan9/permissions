import { useLanguage } from "../i18n/LanguageContext";

// Switches between English and Hebrew; the label is always the language
// you'd switch TO, written in that language.
export default function LanguageToggle() {
  const { lang, setLang, t } = useLanguage();
  return (
    <button
      type="button"
      onClick={() => setLang(lang === "en" ? "he" : "en")}
      className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
    >
      {t("lang.switchTo")}
    </button>
  );
}
