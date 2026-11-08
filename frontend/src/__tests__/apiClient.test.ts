import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError } from "../api/client";
import { useAuthStore } from "../store/authStore";

const user = {
  id: "u1",
  email: "a@acme.test",
  company_id: "acme",
  role: "member",
  is_demo: false,
} as const;

function signIn(expiresIn = 3600) {
  useAuthStore.getState().setSession({
    access_token: "tok-123",
    token_type: "bearer",
    expires_in: expiresIn,
    user,
  });
}

function mockFetch(status: number, body: unknown) {
  const fn = vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fn);
  return fn;
}

function sentHeaders(fn: ReturnType<typeof vi.fn>): Record<string, string> {
  return (fn.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
}

describe("api client", () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.getState().logout();
    // A stale company id from the old header-based flow must not be sent anywhere.
    localStorage.setItem("bidpilot-company", JSON.stringify({ state: { companyId: "acme" } }));
  });

  afterEach(() => vi.unstubAllGlobals());

  it("sends the bearer token and no X-Company-Id header", async () => {
    signIn();
    const fetchMock = mockFetch(200, []);

    await api.get("/tenders");

    const headers = sentHeaders(fetchMock);
    expect(headers.Authorization).toBe("Bearer tok-123");
    expect(headers["X-Company-Id"]).toBeUndefined();
  });

  it("sends no Authorization header when signed out", async () => {
    const fetchMock = mockFetch(200, []);

    await api.get("/tenders");

    expect(sentHeaders(fetchMock).Authorization).toBeUndefined();
  });

  it("does not send an expired token", async () => {
    signIn(-1);
    const fetchMock = mockFetch(200, []);

    await api.get("/tenders");

    expect(sentHeaders(fetchMock).Authorization).toBeUndefined();
  });

  it("clears the session on 401", async () => {
    signIn();
    mockFetch(401, { detail: "Invalid or expired token" });

    await expect(api.get("/auth/me")).rejects.toBeInstanceOf(ApiError);
    expect(useAuthStore.getState().token).toBeNull();
  });

  it("keeps the session on 403 and surfaces the detail", async () => {
    signIn();
    mockFetch(403, { detail: "Insufficient permissions" });

    await expect(api.post("/tenders/ingest")).rejects.toMatchObject({
      status: 403,
      detail: "Insufficient permissions",
    });
    expect(useAuthStore.getState().token).toBe("tok-123");
  });
});
