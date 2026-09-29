export type FormatParams = Record<string, string | number>;

// Fills `{name}` placeholders in a translated template. An unknown
// placeholder is left as-is so a missing param is visible, not silently blank.
export function format(template: string, params: FormatParams = {}): string {
  return template.replace(/\{(\w+)\}/g, (match, key: string) =>
    key in params ? String(params[key]) : match,
  );
}
