import { useEffect, useState } from "react"
import { listarClientes } from "../api"
import type { Cliente } from "../api"
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Users,
  Receipt,
  TrendingUp,
  FileText,
  Activity,
} from "lucide-react"

interface DashboardData {
  totalClientes: number
  clientesRI: number
  clientesMT: number
  comprobantesEsteMes: number
  alertasCriticas: number
  alertasWarning: number
  proximosVencimientos: number
}

export default function Dashboard({ token }: { token: string }) {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    listarClientes(token)
      .then(setClientes)
      .catch(() => setClientes([]))
      .finally(() => setCargando(false))
  }, [token])

  const data: DashboardData = {
    totalClientes: clientes.length,
    clientesRI: clientes.filter((c) => c.condicion_iva === "RI").length,
    clientesMT: clientes.filter((c) => c.condicion_iva === "MT").length,
    comprobantesEsteMes: 0,
    alertasCriticas: 0,
    alertasWarning: 2,
    proximosVencimientos: 4,
  }

  if (cargando) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="rounded-lg border border-border bg-card p-5 animate-pulse">
            <div className="h-4 w-24 bg-muted rounded mb-3" />
            <div className="h-8 w-16 bg-muted rounded" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-[1400px]">
      {/* Hero metrics — bento grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Primary metric */}
        <div className="col-span-1 lg:col-span-2 rounded-lg border border-border bg-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <Users className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium text-muted-foreground">Total clientes</span>
          </div>
          <div className="text-4xl font-semibold tracking-tight text-foreground tabular-data">
            {data.totalClientes}
          </div>
          <div className="mt-3 flex gap-4 text-sm">
            <span className="text-muted-foreground">
              <span className="text-foreground font-medium">{data.clientesRI}</span> RI
            </span>
            <span className="text-muted-foreground">
              <span className="text-foreground font-medium">{data.clientesMT}</span> MT
            </span>
            <span className="text-muted-foreground">
              <span className="text-foreground font-medium">
                {data.totalClientes - data.clientesRI - data.clientesMT}
              </span>{" "}
              Otros
            </span>
          </div>
        </div>

        {/* Secondary: Alertas */}
        <div className="rounded-lg border border-border bg-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium text-muted-foreground">Alertas</span>
          </div>
          <div className="flex items-baseline gap-3">
            <span className="text-3xl font-semibold tracking-tight text-foreground tabular-data">
              {data.alertasCriticas + data.alertasWarning}
            </span>
            {data.alertasCriticas > 0 && (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-red-600 bg-red-50 dark:bg-red-950/30 px-2 py-0.5 rounded">
                <AlertTriangle className="w-3 h-3" />
                {data.alertasCriticas} críticas
              </span>
            )}
          </div>
          {data.alertasWarning > 0 && (
            <p className="mt-2 text-sm text-muted-foreground">{data.alertasWarning} advertencias</p>
          )}
        </div>

        {/* Secondary: Vencimientos */}
        <div className="rounded-lg border border-border bg-card p-5">
          <div className="flex items-center gap-2 mb-3">
            <Clock className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium text-muted-foreground">Vencimientos próximos</span>
          </div>
          <div className="text-3xl font-semibold tracking-tight text-foreground tabular-data">
            {data.proximosVencimientos}
          </div>
          <p className="mt-2 text-sm text-muted-foreground">En los próximos 7 días</p>
        </div>
      </div>

      {/* Second row — action cards + client list */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Quick actions */}
        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Acciones rápidas</h3>
          <div className="space-y-2">
            <QuickAction icon={Receipt} label="Emitir factura" />
            <QuickAction icon={FileText} label="Generar F.931" />
            <QuickAction icon={Upload} label="Subir comprobante" />
            <QuickAction icon={TrendingUp} label="Ver monotributo" />
          </div>
        </div>

        {/* Client list preview */}
        <div className="lg:col-span-2 rounded-lg border border-border bg-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground">Cartera de clientes</h3>
            <span className="text-xs text-muted-foreground">{clientes.length} total</span>
          </div>

          {clientes.length === 0 ? (
            <div className="py-8 text-center">
              <Users className="w-8 h-8 mx-auto text-muted-foreground/50 mb-2" />
              <p className="text-sm text-muted-foreground">Sin clientes registrados</p>
              <p className="text-xs text-muted-foreground mt-1">Agregá un cliente para empezar</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2 px-3 font-medium text-muted-foreground text-xs uppercase tracking-wide">
                      CUIT
                    </th>
                    <th className="text-left py-2 px-3 font-medium text-muted-foreground text-xs uppercase tracking-wide">
                      Razón social
                    </th>
                    <th className="text-left py-2 px-3 font-medium text-muted-foreground text-xs uppercase tracking-wide">
                      IVA
                    </th>
                    <th className="text-left py-2 px-3 font-medium text-muted-foreground text-xs uppercase tracking-wide">
                      Estado
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {clientes.slice(0, 6).map((c) => (
                    <tr key={c.id} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                      <td className="py-2.5 px-3 font-mono text-xs tabular-data">{c.cuit}</td>
                      <td className="py-2.5 px-3 font-medium text-foreground">{c.razon_social}</td>
                      <td className="py-2.5 px-3">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-muted">
                          {c.condicion_iva}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="inline-flex items-center gap-1 text-xs">
                          <CheckCircle2 className="w-3.5 h-3.5 text-green-600" />
                          <span className="text-muted-foreground">Al día</span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {clientes.length > 6 && (
                <p className="mt-3 text-xs text-muted-foreground text-center">
                  +{clientes.length - 6} clientes más
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function QuickAction({ icon: Icon, label }: { icon: React.ElementType; label: string }) {
  return (
    <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm text-foreground hover:bg-muted transition-colors text-left">
      <Icon className="w-4 h-4 text-muted-foreground shrink-0" />
      {label}
    </button>
  )
}

function Upload(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" x2="12" y1="3" y2="15" />
    </svg>
  )
}
