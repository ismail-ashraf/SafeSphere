import {
  Activity,
  BarChart3,
  FileText,
  Image,
  Layers,
  ListChecks,
  Settings,
  ShieldCheck,
} from "lucide-react";

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: BarChart3 },
  { id: "combined", label: "Combined Check", icon: Layers },
  { id: "image", label: "Image Moderation", icon: Image },
  { id: "text", label: "Text Moderation", icon: FileText },
  { id: "review", label: "Review Queue", icon: ListChecks },
  { id: "logs", label: "Moderation Logs", icon: Activity },
  { id: "settings", label: "Settings", icon: Settings },
];

export default function Layout({ activePage, onChangePage, children, health }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><ShieldCheck size={24} /></div>
          <div>
            <strong>SafeSphere</strong>
            <span>AI Moderation</span>
          </div>
        </div>

        <nav className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={`nav-item ${activePage === item.id ? "active" : ""}`}
                onClick={() => onChangePage(item.id)}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-status">
          <div className={`status-dot ${health?.pipeline_ready ? "online" : "warning"}`} />
          <div>
            <strong>{health?.pipeline_ready ? "API Online" : "API Check"}</strong>
            <span>{health?.device ? `Device: ${health.device}` : "Connect backend"}</span>
          </div>
        </div>
      </aside>

      <main className="main-content">{children}</main>
    </div>
  );
}
