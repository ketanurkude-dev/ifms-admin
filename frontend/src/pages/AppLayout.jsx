import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { post } from "../api/apiService";
import { useCurrentAdmin } from "../api/useCurrentAdmin";
import { ApproverIcon, AuditIcon, ProfileIcon, QueueIcon } from "./Icons";

const navItems = [
  { to: "/queue", label: "Review queue", Icon: QueueIcon },
  { to: "/audit-log", label: "Audit log", Icon: AuditIcon },
];

// Shared header + left sidebar nav for every page after login.
export default function AppLayout({ children }) {
  const navigate = useNavigate();
  const admin = useCurrentAdmin();
  const [sidebarVisible, setSidebarVisible] = useState(true);

  async function handleLogout() {
    try {
      await post("/auth/logout");
    } catch {
      // best-effort audit log entry -- logging out proceeds either way
    }
    localStorage.removeItem("access_token");
    navigate("/login");
  }

  const linkClass = ({ isActive }) =>
    `flex items-center gap-3 px-4 py-2.5 text-sm font-medium rounded-md ${
      isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
    }`;

  return (
    <div className="h-screen flex flex-col bg-slate-100">
      <header className="bg-slate-900 text-white shrink-0">
        <div className="px-4 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSidebarVisible(!sidebarVisible)}
              className="mr-1 p-1.5 rounded hover:bg-white/10"
              aria-label="Toggle sidebar"
              title="Toggle sidebar"
            >
              <div className="w-5 h-0.5 bg-white mb-1" />
              <div className="w-5 h-0.5 bg-white mb-1" />
              <div className="w-5 h-0.5 bg-white" />
            </button>
            <div className="w-7 h-7 rounded bg-white/10 border border-white/20 flex items-center justify-center text-xs font-semibold">
              AP
            </div>
            <span className="font-semibold text-sm">Admin Portal</span>
            {admin && (
              <>
                <span className="text-sm text-white/90 ml-3 hidden sm:inline">{admin.name}</span>
                <span className="text-xs text-slate-200 border border-white/20 rounded px-2 py-0.5 ml-2">
                  {admin.role}
                </span>
              </>
            )}
          </div>
          <button onClick={handleLogout} className="text-sm border border-white/30 hover:bg-white/10 px-3 py-1.5 rounded">
            Logout
          </button>
        </div>
        <div className="h-1 bg-amber-500" />
      </header>

      <div className="flex flex-1 min-h-0">
        {sidebarVisible && (
          <aside className="w-56 shrink-0 bg-white border-r border-slate-200 h-full overflow-y-auto p-3">
            <nav className="space-y-1">
              {navItems.map(({ to, label, Icon }) => (
                <NavLink key={to} to={to} className={linkClass}>
                  <Icon style={{ width: 18, height: 18 }} className="shrink-0" />
                  {label}
                </NavLink>
              ))}
            </nav>
            {admin && (
              <div className="mt-6 px-4 py-3 border border-slate-200 rounded-md">
                <div className="flex items-center gap-2 text-xs font-medium text-slate-500 mb-2">
                  <ProfileIcon style={{ width: 14, height: 14 }} />
                  Your permissions
                </div>
                <ul className="space-y-1 text-xs text-slate-600">
                  <li className={admin.can_review_employee ? "text-slate-800" : "text-slate-300 line-through"}>
                    Employee portal
                  </li>
                  <li className={admin.can_review_pension ? "text-slate-800" : "text-slate-300 line-through"}>
                    Pensioner portal
                  </li>
                  <li className={admin.can_review_vendor ? "text-slate-800" : "text-slate-300 line-through"}>
                    Vendor portal
                  </li>
                </ul>
              </div>
            )}
          </aside>
        )}

        <main className="flex-1 min-w-0 h-full overflow-y-auto px-4 sm:px-6 py-6">
          <div className="max-w-5xl mx-auto">{children}</div>
        </main>
      </div>

      <footer className="shrink-0 bg-white border-t border-slate-200 px-4 sm:px-6 py-2 flex items-center justify-end gap-2 text-xs text-slate-400">
        <ApproverIcon style={{ width: 14, height: 14 }} />
        <span>Service-account integration with Employee, Pensioner and Vendor portals</span>
      </footer>
    </div>
  );
}
