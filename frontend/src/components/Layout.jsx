import { NavLink, Outlet, useLocation } from "react-router-dom";
import DateRangeBar from "@/components/DateRangeBar";
import { TelemetryRunner } from "@/components/TelemetryRunner";
import { ThemeToggle } from "@/components/ThemeToggle";
import { CompanyName } from "@/components/CompanyName";
import { ManageEntries } from "@/components/ManageEntries";
import { useState } from "react";
import {
  LayoutDashboard, TrendingUp, Receipt, Fuel, Truck, PackageCheck, Users, ShieldAlert, Database, LogOut, Menu, X, Trophy, UserCog, FileText, Radio, HardDriveDownload, UserPlus, Palette,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, id: "dashboard" },
  { to: "/income", label: "Income", icon: TrendingUp, id: "income" },
  { to: "/expenses", label: "Expenses", icon: Receipt, id: "expenses" },
  { to: "/fuel", label: "Fuel & MPG", icon: Fuel, id: "fuel" },
  { to: "/trucks", label: "Trucks", icon: Truck, id: "trucks" },
  { to: "/loads", label: "Loads", icon: PackageCheck, id: "loads" },
  { to: "/telemetry", label: "Live Telemetry", icon: Radio, id: "telemetry" },
  { to: "/drivers", label: "Drivers", icon: Users, id: "drivers" },
  { to: "/leaderboard", label: "Leaderboard", icon: Trophy, id: "leaderboard" },
  { to: "/inspections", label: "DOT Inspections", icon: ShieldAlert, id: "inspections" },
  { to: "/users", label: "Users", icon: UserCog, id: "users", owner: true },
  { to: "/users/new", label: "Create User", icon: UserPlus, id: "create-user", owner: true },
  { to: "/company", label: "Company & Colors", icon: Palette, id: "company", owner: true },
  { to: "/report", label: "Monthly Report", icon: FileText, id: "report" },
  { to: "/backup", label: "Backup & Restore", icon: HardDriveDownload, id: "backup", owner: true },
  { to: "/test-data", label: "Test Data", icon: Database, id: "test-data", owner: true },
];

function Sidebar({ onNavigate, mobile = false }) {
  const { user, logout, isOwner } = useAuth();
  return (
    <div className="flex h-full flex-col">
      <div className="px-6 pb-8 pt-7">
        <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-500">Virtual Trucking Co.</div>
        <div className="font-heading text-2xl font-black text-foreground"><CompanyName testId={mobile ? "brand-name-mobile-sidebar" : "brand-name"} /></div>
      </div>
      <nav className="min-h-0 flex-1 space-y-1 overflow-y-auto px-3 pb-3">
        {NAV.filter((n) => isOwner || !n.owner).map(({ to, label, icon: Icon, id }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/" || to === "/users"}
            onClick={onNavigate}
            data-testid={`nav-${id}`}
            className={({ isActive }) =>
              `group flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors duration-150 ${
                isActive ? "bg-blue-500/10 text-blue-400 shadow-[inset_3px_0_0_#3B82F6]" : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-100"
              }`
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-slate-800 p-4">
        <div className="mb-3"><ThemeToggle testId={mobile ? "mobile-theme-toggle" : "theme-toggle"} /></div>
        <div className="mb-3 font-mono text-xs text-slate-500">
          Signed in as <span className="text-slate-300" data-testid="current-username">{user?.username}</span>
          <span data-testid="current-role" className="ml-2 rounded bg-red-500/10 px-1.5 py-0.5 text-[10px] uppercase text-red-400">{user?.role}</span>
        </div>
        <button
          data-testid="logout-btn"
          onClick={logout}
          className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-slate-400 transition-colors hover:bg-rose-500/10 hover:text-rose-400"
        >
          <LogOut className="h-4 w-4" /> Log out
        </button>
      </div>
    </div>
  );
}

const NO_RANGE = ["/leaderboard", "/users", "/users/new", "/test-data", "/report", "/telemetry", "/backup", "/company"];

export default function Layout() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-100">
      <TelemetryRunner />
      <aside className="no-print fixed inset-y-0 left-0 z-40 hidden w-64 border-r border-slate-800 bg-[#080B12] lg:block">
        <Sidebar />
      </aside>
      <div className="no-print sticky top-0 z-30 flex items-center justify-between border-b border-slate-800 bg-[#080B12]/90 px-4 py-3 backdrop-blur-md lg:hidden">
        <div className="min-w-0 pr-3 font-heading text-lg font-black"><CompanyName testId="brand-name-mobile" /></div>
        <button data-testid="mobile-menu-btn" onClick={() => setOpen(true)} className="p-2 text-slate-300"><Menu /></button>
      </div>
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-64 border-r border-slate-800 bg-[#080B12]">
            <button data-testid="mobile-menu-close" onClick={() => setOpen(false)} className="absolute right-3 top-3 p-2 text-slate-400"><X className="h-4 w-4" /></button>
            <Sidebar mobile onNavigate={() => setOpen(false)} />
          </aside>
        </div>
      )}
      <main className="lg:pl-64">
        <div className="mx-auto max-w-[1500px] px-4 py-8 sm:px-8 lg:px-12 lg:py-10">
          <ManageEntries />
          {!NO_RANGE.includes(pathname) && <DateRangeBar />}
          <Outlet />
        </div>
      </main>
    </div>
  );
}
