const BASE_URL = (import.meta.env.VITE_API_BASE as string | undefined) ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly detail: string,
    public readonly status: number,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

function getCompanyId(): string | null {
  try {
    const raw = localStorage.getItem("bidpilot-company");
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { state?: { companyId?: string } };
    return parsed.state?.companyId ?? null;
  } catch {
    return null;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const companyId = getCompanyId();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (companyId) headers["X-Company-Id"] = companyId;

  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { ...headers, ...(init?.headers as Record<string, string> | undefined) },
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // ignore parse error
    }
    throw new ApiError(detail, response.status);
  }

  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
};
