import { en } from "./en";
import type { Messages } from "./en";
import { he } from "./he";

export type Language = "en" | "he";

export const RTL_LANGUAGES: ReadonlySet<Language> = new Set<Language>(["he"]);

// Untranslated keys fall back to English.
const MESSAGES: Record<Language, Messages> = { en, he: { ...en, ...he } };

export function messagesFor(lang: Language): Messages {
  return MESSAGES[lang];
}
