import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";
import { RequireAuth } from "../components/auth/RequireAuth";
import { useAuthStore } from "../store/authStore";

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/login" element={<p>login page</p>} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <p>protected</p>
            </RequireAuth>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("RequireAuth", () => {
  beforeEach(() => useAuthStore.getState().logout());

  it("redirects to /login without a session", () => {
    renderAt("/");
    expect(screen.getByText("login page")).toBeInTheDocument();
  });

  it("renders children with a valid session", () => {
    useAuthStore.getState().setSession({
      access_token: "t",
      token_type: "bearer",
      expires_in: 60,
      user: { id: "u", email: "e@x.test", company_id: "c", role: "viewer", is_demo: true },
    });
    renderAt("/");
    expect(screen.getByText("protected")).toBeInTheDocument();
  });
});
