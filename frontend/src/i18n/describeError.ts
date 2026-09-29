import { ApiError } from "../api/client";
import type { ResourceType } from "../api/client";
import type { MessageKey, Messages } from "./en";
import { format } from "./format";
import type { FormatParams } from "./format";
import { TYPE_LABEL_KEYS } from "./labels";

// Generic message per HTTP status, used when the backend sent no code (or
// one this UI has no translation for yet).
const STATUS_FALLBACK_KEYS: Record<number, MessageKey> = {
  401: "errors.unauthorized",
  403: "errors.forbidden",
  404: "errors.not_found",
  409: "errors.conflict",
  422: "errors.validation",
};

function isMessageKey(messages: Messages, key: string): key is MessageKey {
  return key in messages;
}

function isResourceType(value: string): value is ResourceType {
  return value in TYPE_LABEL_KEYS;
}

// Error params arrive as raw backend values (e.g. `{child: "map"}`); a
// resource-type value is shown as its translated label instead.
function localizeParams(messages: Messages, params: FormatParams): FormatParams {
  const result: FormatParams = {};
  for (const [key, value] of Object.entries(params)) {
    result[key] =
      typeof value === "string" && isResourceType(value) ? messages[TYPE_LABEL_KEYS[value]] : value;
  }
  return result;
}

// Turns any caught error into a user-facing message in the active language:
// the backend's specific `code` first, then a generic per-status message,
// then the caller's own fallback. The backend's English `detail` is never
// shown — it's there for API callers, not this UI.
export function describeError(messages: Messages, error: unknown, fallback: MessageKey): string {
  if (!(error instanceof ApiError)) return messages[fallback];

  const codeKey = `errors.${error.code ?? ""}`;
  if (error.code && isMessageKey(messages, codeKey)) {
    return format(messages[codeKey], localizeParams(messages, error.params));
  }
  const statusKey = STATUS_FALLBACK_KEYS[error.status];
  return messages[statusKey ?? fallback];
}
