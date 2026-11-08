import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { authApi } from "../api/auth";
import { ApiError } from "../api/client";
import type { TokenResponse } from "../api/types";
import { useSessionActions } from "../hooks/useSession";
import { isAuthenticated } from "../store/authStore";

const DEMO_ENABLED = import.meta.env.VITE_DEMO_ENABLED === "true";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { start } = useSessionActions();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as { from?: string } | null)?.from ?? "/";

  if (isAuthenticated()) return <Navigate to={from} replace />;

  async function signIn(call: () => Promise<TokenResponse>) {
    setBusy(true);
    setError(null);
    try {
      start(await call());
      navigate(from, { replace: true });
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Sign-in failed");
    } finally {
      setBusy(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    void signIn(() => authApi.login(email, password));
  }

  const inputClass =
    "w-full rounded-md border border-[#1e2530] bg-[#0f1117] px-3 py-2 text-sm text-[#e8eaed] outline-none focus:border-[#c9a84c]/50";

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0f1117] px-4">
      <div className="w-full max-w-sm rounded-lg border border-[#1e2530] bg-[#161a22] p-6">
        <h1 className="text-lg font-semibold tracking-wide text-[#c9a84c]">BidPilot</h1>
        <p className="mt-1 text-xs text-[#8b93a0]">Tender intelligence for suppliers</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-3">
          <div>
            <label htmlFor="email" className="mb-1 block text-xs text-[#8b93a0]">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label htmlFor="password" className="mb-1 block text-xs text-[#8b93a0]">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
            />
          </div>

          {error && (
            <p role="alert" className="text-xs text-red-400">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-md bg-[#c9a84c] py-2 text-sm font-medium text-[#0f1117] transition-colors hover:bg-[#a07c34] disabled:opacity-50"
          >
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>

        {DEMO_ENABLED && (
          <button
            type="button"
            disabled={busy}
            onClick={() => void signIn(authApi.demo)}
            className="mt-3 w-full rounded-md border border-[#c9a84c]/40 py-2 text-sm text-[#c9a84c] transition-colors hover:bg-[#c9a84c]/10 disabled:opacity-50"
          >
            Try the demo
          </button>
        )}
      </div>
    </div>
  );
}
