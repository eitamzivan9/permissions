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

export type SystemRole = "super_editor" | "super_viewer";

// Only /auth/me returns this (who am I + my system-wide roles) — every other
// user-listing endpoint returns a plain MockUser.
export interface Me extends MockUser {
  system_roles: SystemRole[];
}

export function isSuperEditor(user: Me | null): boolean {
  return user !== null && user.system_roles.includes("super_editor");
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
  search?: string;
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

// Same shape as Grant, but a Restriction means the opposite thing: an
// explicit whitelist. The moment any restriction row exists on a resource
// (at any level up the tree), only grantees listed there keep access —
// admin-only to set.
export interface Restriction {
  grantee_type: GranteeType;
  user_id: string | null;
  team_id: string | null;
  resource_id: string;
  role: Role;
  granted_by: string;
}

export interface SetRestrictionParams {
  resourceId: string;
  granteeType: GranteeType;
  granteeId: string;
  role: Role;
}

export interface DeleteRestrictionParams {
  resourceId: string;
  granteeType: GranteeType;
  granteeId: string;
}

// One shape for every level of the resource tree, mirroring the backend's
// Resource entity (owner_id is set only on a lazily-created personal workspace).
export interface Resource {
  id: string;
  type: ResourceType;
  name: string;
  parent_id: string | null;
  inherits_from_parent: boolean;
  owner_id: string | null;
}

export interface CreateResourceParams {
  type: ResourceType;
  name: string;
  parentId: string;
}

export interface CreateTeamWorkspaceParams {
  name: string;
  adminUserId: string;
}

export interface MoveResourceParams {
  resourceId: string;
  newParentId: string;
}

// A grantee resolved to a display name — see GET /access/admins/{id}.
export interface GranteeInfo {
  grantee_type: GranteeType;
  id: string;
  name: string;
}

const ROLE_RANK: Record<Role, number> = { viewer: 1, editor: 2, manager: 3, admin: 4 };

export function roleAtLeast(role: Role | null, threshold: Role): boolean {
  return role !== null && ROLE_RANK[role] >= ROLE_RANK[threshold];
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

export function getMe(): Promise<Me> {
  return request<Me>("/auth/me");
}

// ---------------------------------------------------------------------------
// Catalog endpoint
// ---------------------------------------------------------------------------

export function getCatalog(params: GetCatalogParams = {}): Promise<CatalogPage> {
  const qs = buildQueryString({
    search: params.search,
    page: params.page,
    page_size: params.page_size,
  });
  return request<CatalogPage>(`/catalog${qs}`);
}

// ---------------------------------------------------------------------------
// Grants endpoints
// ---------------------------------------------------------------------------

export function getManageableUsers(resourceId?: string): Promise<MockUser[]> {
  const qs = buildQueryString({ resource_id: resourceId });
  return request<MockUser[]>(`/grants/manageable-users${qs}`);
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
// Restrictions endpoints (Admin-only whitelist gate — see Restriction above)
// ---------------------------------------------------------------------------

export function getRestrictionsForResource(resourceId: string): Promise<Restriction[]> {
  return request<Restriction[]>(`/restrictions/${resourceId}`);
}

export function setRestriction(params: SetRestrictionParams): Promise<Restriction> {
  return request<Restriction>(
    `/restrictions/${params.resourceId}/${params.granteeType}/${params.granteeId}`,
    { method: "PUT", body: JSON.stringify({ role: params.role }) },
  );
}

export function deleteRestriction(params: DeleteRestrictionParams): Promise<void> {
  return request<void>(
    `/restrictions/${params.resourceId}/${params.granteeType}/${params.granteeId}`,
    { method: "DELETE" },
  );
}

// ---------------------------------------------------------------------------
// Access-transparency endpoints
// ---------------------------------------------------------------------------

// Every grantee that currently resolves to Admin at the nearest ancestor
// gating this resource — who to ask when effective_role here is null.
export function getResourceAdmins(resourceId: string): Promise<GranteeInfo[]> {
  return request<GranteeInfo[]>(`/access/admins/${resourceId}`);
}

// ---------------------------------------------------------------------------
// Teams endpoint (read-only from the UI's side — grants can target an
// existing Team; creating/managing Team membership isn't part of UI scope)
// ---------------------------------------------------------------------------

export function listTeams(): Promise<Team[]> {
  return request<Team[]>("/teams");
}

// ---------------------------------------------------------------------------
// Resources endpoints
// ---------------------------------------------------------------------------

export function getMyWorkspace(): Promise<Resource> {
  return request<Resource>("/resources/my-workspace");
}

export function createTeamWorkspace(params: CreateTeamWorkspaceParams): Promise<Resource> {
  return request<Resource>("/resources/workspaces", {
    method: "POST",
    body: JSON.stringify({ name: params.name, admin_user_id: params.adminUserId }),
  });
}

export function createResource(params: CreateResourceParams): Promise<Resource> {
  return request<Resource>("/resources", {
    method: "POST",
    body: JSON.stringify({ type: params.type, name: params.name, parent_id: params.parentId }),
  });
}

export function moveResource(params: MoveResourceParams): Promise<Resource> {
  return request<Resource>(`/resources/${params.resourceId}/move`, {
    method: "PATCH",
    body: JSON.stringify({ new_parent_id: params.newParentId }),
  });
}

// Admin-only. For Workspace/Folder/Group, only succeeds when resourceId has
// zero children (409 otherwise) — this server doesn't own Map/Layer data, so
// it never bulk-deletes it via a folder-level delete. Map/Layer still
// cascade-delete their whole subtree along with every grant/restriction in
// it, unconditionally — but the frontend never calls this for Map/Layer
// (see "Remove access" via deleteGrant instead); this path stays for the
// future server-to-server flow. Irreversible, no confirmation at this layer.
export function deleteResource(resourceId: string): Promise<void> {
  return request<void>(`/resources/${resourceId}`, { method: "DELETE" });
}
