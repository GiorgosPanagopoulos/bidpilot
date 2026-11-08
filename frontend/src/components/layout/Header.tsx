import { Building2, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useSessionActions } from "../../hooks/useSession";
import { useAuthStore } from "../../store/authStore";
import { useCompanyStore } from "../../store/companyStore";

export function Header() {
  const profile = useCompanyStore((s) => s.profile);
  const user = useAuthStore((s) => s.user);
  const { logout } = useSessionActions();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="flex h-14 items-center justify-between border-b border-[#1e2530] bg-[#161a22] px-6">
      <div className="flex items-center gap-3">
        <img
          src="/bidpilot-logo.png"
          alt="BidPilot"
          className="h-7"
          onError={(e) => {
            (e.currentTarget as HTMLImageElement).style.display = "none";
          }}
        />
        <span className="text-sm font-semibold tracking-wide text-[#c9a84c]">BidPilot</span>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 rounded-md border border-[#1e2530] px-3 py-1.5 text-sm text-[#8b93a0]">
          <Building2 size={14} />
          <span>{profile?.name ?? user?.company_id ?? ""}</span>
        </div>
        {user && (
          <span className="text-xs text-[#8b93a0]">
            {user.email} · {user.role}
            {user.is_demo && (
              <span className="ml-2 rounded bg-[#c9a84c]/15 px-1.5 py-0.5 text-[#c9a84c]">
                demo
              </span>
            )}
          </span>
        )}
        <button
          onClick={handleLogout}
          aria-label="Sign out"
          className="rounded-md p-1.5 text-[#8b93a0] transition-colors hover:text-[#e8eaed]"
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  );
}
