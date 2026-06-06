import { BarChart3, BriefcaseBusiness, Rss } from "lucide-react";
import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Feed", icon: Rss },
  { to: "/workspace", label: "Workspace", icon: BriefcaseBusiness },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
];

export function Sidebar() {
  return (
    <nav className="flex h-full w-56 shrink-0 flex-col border-r border-[#1e2530] bg-[#161a22] px-3 py-6">
      {links.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === "/"}
          className={({ isActive }) =>
            `mb-1 flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors ${
              isActive
                ? "bg-[#c9a84c]/10 text-[#c9a84c]"
                : "text-[#8b93a0] hover:bg-[#1e2530] hover:text-[#e8eaed]"
            }`
          }
        >
          <Icon size={16} />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
