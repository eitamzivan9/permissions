// The only module that knows the backend's base URL, request/response shapes,
// and how auth tokens are attached/stored. Every other file talks to the
// backend exclusively through the typed functions exported here.

const API_BASE = "/api";
const TOKEN_STORAGE_KEY = "permissions_server.token";

// ---------------------------------------------------------------------------
// Shared types (mirror the backend's Python enums/schemas by value)
// ---------------------------------------------------------------------------

export type Role = "viewer" | "editor" | "manager" | "admin";
export type ResourceType = "workspace" | "folder" | "map" | "group" | "layer";
export type GranteeType = "user" | "team";

export interface MockUser {
  id: string;
  name: string;
  email: string;
}

export interface Team {
  id: string;
  name: string;
}

export interface LoginResponse {
  token: string;
}

// One shape for every level of the resource tree — mirrors the backend's
// single Resource/CatalogItem model (no separate Map/Layer types).
export interface CatalogItem {
  id: string;
  type: ResourceType;
  name: string;
  effective_role: Role | null;
  can_manage: boolean;
  can_fetch: boolean;
  children: CatalogItem[];
}

export interface CatalogPage {
  items: CatalogItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface GetCatalogParams {
  q?: string;
  page?: number;
  page_size?: number;
}

export interface Grant {
  grantee_type: GranteeType;
  user_id: string | null;
  team_id: string | null;
  resource_id: string;
  role: Role;
  granted_by: string;
}

export interface SetGrantParams {
  resourceId: string;
  granteeType: GranteeType;
  granteeId: string;
  role: Role;
}

export interface DeleteGrantParams {
  resourceId: string;
  granteeType: GranteeType;
  granteeId: string;
}

// ---------------------------------------------------------------------------
// Typed errors — callers distinguish 401 (redirect to login) vs 403 (show error)
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export class UnauthorizedError extends ApiError {
  constructor(message = "Your session has expired. Please log in again.") {
    super(401, message);
    this.name = "UnauthorizedError";
  }
}

export class ForbiddenError extends ApiError {
  constructor(message = "You are not authorized to perform this action.") {
    super(403, message);
    this.name = "ForbiddenError";
  }
}

// ---------------------------------------------------------------------------
// Token storage (sessionStorage-backed; AuthContext is the sole consumer of
// these three helpers so the storage key/shape stays defined in one place)
// ---------------------------------------------------------------------------

export function getStoredToken(): string | null {
  return sessionStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string): void {
  sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearStoredToken(): void {
  sessionStorage.removeItem(TOKEN_STORAGE_KEY);
}

// ---------------------------------------------------------------------------
// Core request helper
// ---------------------------------------------------------------------------

async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (
      body !== null &&
      typeof body === "object" &&
      "detail" in body &&
      typeof (body as { detail: unknown }).detail === "string"
    ) {
      return (body as { detail: string }).detail;
    }
  } catch {
    // response body wasn't JSON (or was empty) — fall through to the default
  }
  return response.statusText || `Request failed with status ${response.status}`;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (response.status === 401) {
    throw new UnauthorizedError(await extractErrorMessage(response));
  }
  if (response.status === 403) {
    throw new ForbiddenError(await extractErrorMessage(response));
  }
  if (!response.ok) {
    throw new ApiError(response.status, await extractErrorMessage(response));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function buildQueryString(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

// ---------------------------------------------------------------------------
// Auth endpoints
// ---------------------------------------------------------------------------

export function listMockUsers(): Promise<MockUser[]> {
  return request<MockUser[]>("/auth/mock-users");
}

export function login(userId: string): Promise<LoginResponse> {
  return request<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ user_id: userId }),
  });
}

export function getMe(): Promise<MockUser> {
  return request<MockUser>("/auth/me");
}

// ---------------------------------------------------------------------------
// Catalog endpoint
// ---------------------------------------------------------------------------

export function getCatalog(params: GetCatalogParams = {}): Promise<CatalogPage> {
  const qs = buildQueryString({
    q: params.q,
    page: params.page,
    page_size: params.page_size,
  });
  return request<CatalogPage>(`/catalog${qs}`);
}

// ---------------------------------------------------------------------------
// Grants endpoints
// ---------------------------------------------------------------------------

export function getManageableUsers(): Promise<MockUser[]> {
  return request<MockUser[]>("/grants/manageable-users");
}

export function getGrantsForResource(resourceId: string): Promise<Grant[]> {
  return request<Grant[]>(`/grants/${resourceId}`);
}

export function setGrant(params: SetGrantParams): Promise<Grant> {
  return request<Grant>(`/grants/${params.resourceId}/${params.granteeType}/${params.granteeId}`, {
    method: "PUT",
    body: JSON.stringify({ role: params.role }),
  });
}

export function deleteGrant(params: DeleteGrantParams): Promise<void> {
  return request<void>(`/grants/${params.resourceId}/${params.granteeType}/${params.granteeId}`, {
    method: "DELETE",
  });
}

// ---------------------------------------------------------------------------
// Teams endpoint (read-only from the UI's side — grants can target an
// existing Team; creating/managing Team membership isn't part of UI scope)
// ---------------------------------------------------------------------------

export function listTeams(): Promise<Team[]> {
  return request<Team[]>("/teams");
}
