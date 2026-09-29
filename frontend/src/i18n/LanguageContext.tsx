import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { describeError as describeErrorWith } from "./describeError";
import type { MessageKey } from "./en";
import { format } from "./format";
import type { FormatParams } from "./format";
import { messagesFor, RTL_LANGUAGES } from "./messages";
import type { Language } from "./messages";
const LANGUAGE_STORAGE_KEY = "permissions_server.lang";

// Base names of plural key pairs (`x.one` + `x.other`) — see tPlural.
type PluralBaseOf<K> = K extends `${infer Base}.one`
  ? `${Base}.other` extends MessageKey
    ? Base
    : never
  : never;
type PluralBase = PluralBaseOf<MessageKey>;

interface LanguageContextValue {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: MessageKey, params?: FormatParams) => string;
  /** Picks `<base>.one` or `<base>.other` for `count`; `{count}` is filled in. */
  tPlural: (base: PluralBase, count: number, params?: FormatParams) => string;
  /** User-facing message for a caught error, in the active language. */
  describeError: (error: unknown, fallback: MessageKey) => string;
}

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

function readStoredLanguage(): Language {
  try {
    const stored = localStorage.getItem(LANGUAGE_STORAGE_KEY);
    return stored === "he" || stored === "en" ? stored : "en";
  } catch {
    return "en";
  }
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Language>(readStoredLanguage);

  // `dir` on <html> is what flips the whole layout — Tailwind's logical
  // utilities (ms-/ps-/border-s/text-start) and flex order follow it.
  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = RTL_LANGUAGES.has(lang) ? "rtl" : "ltr";
  }, [lang]);

  const setLang = useCallback((next: Language) => {
    setLangState(next);
    try {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, next);
    } catch {
      // storage unavailable (private mode etc.) — the choice just won't persist
    }
  }, []);

  const value = useMemo<LanguageContextValue>(() => {
    const messages = messagesFor(lang);
    const pluralRules = new Intl.PluralRules(lang);
    const t = (key: MessageKey, params?: FormatParams) => format(messages[key], params);
    return {
      lang,
      setLang,
      t,
      tPlural: (base, count, params) => {
        const form = pluralRules.select(count) === "one" ? "one" : "other";
        return t(`${base}.${form}` as MessageKey, { ...params, count });
      },
      describeError: (error, fallback) => describeErrorWith(messages, error, fallback),
    };
  }, [lang, setLang]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage(): LanguageContextValue {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
}
