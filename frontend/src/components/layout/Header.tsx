import { Building2, ChevronDown } from "lucide-react";
import { useCompanyStore } from "../../store/companyStore";

export function Header() {
  const profile = useCompanyStore((s) => s.profile);

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

      <button className="flex items-center gap-2 rounded-md border border-[#1e2530] px-3 py-1.5 text-sm text-[#8b93a0] hover:border-[#c9a84c]/40 hover:text-[#e8eaed] transition-colors">
        <Building2 size={14} />
        <span>{profile?.name ?? "Select company"}</span>
        <ChevronDown size={12} />
      </button>
    </header>
  );
}
