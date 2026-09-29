import { describe, expect, it } from "vitest";
import { ApiError } from "../api/client";
import { describeError } from "./describeError";
import { en } from "./en";
import type { MessageKey } from "./en";
import { format } from "./format";
import { he } from "./he";
import { messagesFor, RTL_LANGUAGES } from "./messages";

function placeholders(template: string): string[] {
  return [...template.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
}

function apiError(status: number, code: string | null, params = {}): ApiError {
  return new ApiError(status, { message: "english detail", code, params });
}

describe("format", () => {
  it("fills placeholders", () => {
    expect(format("Hi {name}, {count} left", { name: "דנה", count: 3 })).toBe("Hi דנה, 3 left");
  });

  it("leaves an unknown placeholder visible instead of blank", () => {
    expect(format("Hi {name}")).toBe("Hi {name}");
  });
});

describe("dictionaries", () => {
  it("Hebrew only uses keys that exist in English", () => {
    for (const key of Object.keys(he)) {
      expect(en).toHaveProperty(key);
    }
  });

  it("every Hebrew value keeps exactly the English placeholders", () => {
    for (const [key, value] of Object.entries(he)) {
      // A singular form may spell out "one" (e.g. "תוצאה אחת") instead of {count}.
      const expected = placeholders(en[key as MessageKey]).filter(
        (name) => !(key.endsWith(".one") && name === "count"),
      );
      const actual = placeholders(value).filter(
        (name) => !(key.endsWith(".one") && name === "count"),
      );
      expect(actual, key).toEqual(expected);
    }
  });

  it("values hold words only — shared decorative symbols live in the JSX", () => {
    for (const dict of [en, he]) {
      for (const [key, value] of Object.entries(dict)) {
        expect(value.startsWith("+ "), key).toBe(false);
        expect(value.endsWith("…"), key).toBe(false);
        expect(/^\(.*\)$/.test(value), key).toBe(false);
      }
    }
  });

  it("uses distinct Hebrew labels for every role", () => {
    const roles = ["role.viewer", "role.editor", "role.manager", "role.admin"] as const;
    const labels = roles.map((key) => messagesFor("he")[key]);
    expect(new Set(labels).size).toBe(roles.length);
    expect(messagesFor("he")["role.manager"]).toBe("מנהל");
    expect(messagesFor("he")["role.admin"]).toBe("אדמין");
  });
});

describe("messagesFor", () => {
  it("returns English as-is", () => {
    expect(messagesFor("en")).toBe(en);
  });

  it("falls back to English for any key Hebrew doesn't translate", () => {
    const hebrew = messagesFor("he");
    for (const key of Object.keys(en) as MessageKey[]) {
      expect(hebrew[key], key).toBe(he[key] ?? en[key]);
    }
  });

  it("marks only Hebrew as right-to-left", () => {
    expect(RTL_LANGUAGES.has("he")).toBe(true);
    expect(RTL_LANGUAGES.has("en")).toBe(false);
  });
});

describe("describeError", () => {
  const hebrew = messagesFor("he");

  it("translates a specific backend code in the active language", () => {
    const error = apiError(409, "move_into_own_subtree");
    expect(describeError(en, error, "node.moveFailed")).toBe(en["errors.move_into_own_subtree"]);
    expect(describeError(hebrew, error, "node.moveFailed")).toBe(
      hebrew["errors.move_into_own_subtree"],
    );
  });

  it("translates resource-type params and fills numeric params", () => {
    const typeError = apiError(409, "invalid_child_type", { child: "workspace", parent: "folder" });
    expect(describeError(en, typeError, "node.moveFailed")).toBe(
      "A Workspace can't be placed inside a Folder.",
    );
    expect(describeError(hebrew, typeError, "node.moveFailed")).toBe(
      "לא ניתן למקם סביבת עבודה בתוך תיקייה.",
    );

    const countError = apiError(409, "delete_not_empty", { count: 3 });
    expect(describeError(hebrew, countError, "info.deleteFailed")).toContain("3");
  });

  it.each([
    [401, "errors.unauthorized"],
    [403, "errors.forbidden"],
    [404, "errors.not_found"],
    [409, "errors.conflict"],
    [422, "errors.validation"],
  ] as const)("falls back to the generic %i message for an unknown code", (status, key) => {
    expect(describeError(hebrew, apiError(status, "some_future_code"), "info.deleteFailed")).toBe(
      hebrew[key],
    );
    expect(describeError(hebrew, apiError(status, null), "info.deleteFailed")).toBe(hebrew[key]);
  });

  it("uses the caller's fallback for an unmapped status or a non-API error", () => {
    expect(describeError(hebrew, apiError(500, null), "info.deleteFailed")).toBe(
      hebrew["info.deleteFailed"],
    );
    expect(describeError(hebrew, new TypeError("network down"), "info.deleteFailed")).toBe(
      hebrew["info.deleteFailed"],
    );
  });

  it("never shows the backend's English detail", () => {
    const shown = describeError(hebrew, apiError(403, "forbidden"), "info.deleteFailed");
    expect(shown).not.toContain("english detail");
  });
});
