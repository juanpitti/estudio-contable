import { useState, type ReactNode } from "react"
import {
  LayoutDashboard,
  Upload,
  Users,
  Receipt,
  TrendingUp,
  FileText,
  Map,
  Calculator,
  Shuffle,
  Bot,
  LogOut,
  Moon,
  Sun,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"
import { useTheme } from "./ui/theme-provider"

export type Solapa =
  | "dashboard"
  | "subir"
  | "clientes"
  | "facturacion"
  | "monotributo"
  | "f931"
  | "convenio"
  | "liquidacion"
  | "conciliacion"
  | "asistente"

const NAV_ITEMS: { id: Solapa; label: string; icon: React.ElementType }[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "clientes", label: "Clientes", icon: Users },
  { id: "subir", label: "Subir factura", icon: Upload },
  { id: "facturacion", label: "Facturación", icon: Receipt },
  { id: "liquidacion", label: "Liquidación IVA", icon: Calculator },
  { id: "monotributo", label: "Monotributo", icon: TrendingUp },
  { id: "f931", label: "F.931", icon: FileText },
  { id: "convenio", label: "Convenio", icon: Map },
  { id: "conciliacion", label: "Conciliación", icon: Shuffle },
  { id: "asistente", label: "Asistente", icon: Bot },
]

interface AppLayoutProps {
  children: ReactNode
  activeTab: Solapa
  onTabChange: (tab: Solapa) => void
  onLogout: () => void
}

export default function AppLayout({ children, activeTab, onTabChange, onLogout }: AppLayoutProps) {
  const { isDark, toggle } = useTheme()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="min-h-screen flex bg-surface-canvas text-foreground">
      {/* Sidebar */}
      <aside
        className="flex flex-col border-r border-border bg-sidebar-background transition-[width] duration-fast"
        style={{ width: collapsed ? 56 : 240 }}
      >
        {/* Logo area */}
        <div className="h-14 flex items-center px-3 border-b border-sidebar-border shrink-0">
          <div className="w-8 h-8 rounded-md bg-primary flex items-center justify-center shrink-0">
            <span className="text-primary-foreground font-bold text-sm">EC</span>
          </div>
          {!collapsed && (
            <span className="ml-3 font-semibold text-sm tracking-tight truncate">Estudio</span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon
            const isActive = activeTab === item.id
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center gap-3 px-2.5 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/50"
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon className="w-[18px] h-[18px] shrink-0" strokeWidth={isActive ? 2.5 : 2} />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </button>
            )
          })}
        </nav>

        {/* Bottom actions */}
        <div className="p-2 border-t border-sidebar-border shrink-0 space-y-1">
          <button
            onClick={toggle}
            className="w-full flex items-center gap-3 px-2.5 py-2 rounded-md text-sm text-sidebar-foreground hover:bg-sidebar-accent/50 transition-colors"
            title={collapsed ? (isDark ? "Modo claro" : "Modo oscuro") : undefined}
          >
            {isDark ? (
              <Sun className="w-[18px] h-[18px] shrink-0" />
            ) : (
              <Moon className="w-[18px] h-[18px] shrink-0" />
            )}
            {!collapsed && <span>{isDark ? "Modo claro" : "Modo oscuro"}</span>}
          </button>
          <button
            onClick={onLogout}
            className="w-full flex items-center gap-3 px-2.5 py-2 rounded-md text-sm text-sidebar-foreground hover:bg-sidebar-accent/50 transition-colors"
            title={collapsed ? "Cerrar sesión" : undefined}
          >
            <LogOut className="w-[18px] h-[18px] shrink-0" />
            {!collapsed && <span>Cerrar sesión</span>}
          </button>

          {/* Collapse toggle */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center justify-center py-1 rounded-md text-sidebar-foreground hover:bg-sidebar-accent/50 transition-colors mt-1"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="h-14 flex items-center justify-between px-6 border-b border-border bg-surface-raised shrink-0">
          <h2 className="text-sm font-medium text-foreground">
            {NAV_ITEMS.find((n) => n.id === activeTab)?.label}
          </h2>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground">{new Date().toLocaleDateString("es-AR")}</span>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  )
}
