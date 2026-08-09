import { useEffect, useState } from "react"

interface ClienteSemaforo {
  id: number
  razon_social: string
  cuit: string
  condicion_iva: string
  semaforo: "verde" | "amarillo" | "rojo"
  ultima_revision: string | null
}

interface Vencimiento {
  impuesto: string
  fecha: string
  periodicidad: string
}

interface Alerta {
  impuesto: string
  fecha: string
  dias_restantes: number
  nivel: string
  mensaje: string
}

interface DashboardData {
  clientes: ClienteSemaforo[]
  vencimientos_proximos: Vencimiento[]
  alertas: Alerta[]
}

export default function Dashboard({ token }: { token: string }) {
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState("")
  const [cargando, setCargando] = useState(true)

  async function cargar() {
    setCargando(true)
    try {
      const r = await fetch("/dashboard", { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error("Error al cargar dashboard")
      setData(await r.json())
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error")
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => { cargar() }, [token])

  if (cargando) return <p className="text-slate-500">Cargando…</p>
  if (error) return <p className="text-red-600">{error}</p>
  if (!data) return null

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-xl shadow-md p-6">
        <h2 className="font-semibold text-slate-800 mb-4">Cartera</h2>
        {data.clientes.length === 0 ? (
          <p className="text-sm text-slate-400">No hay clientes cargados.</p>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {data.clientes.map((c) => (
              <div key={c.id} className="flex items-center justify-between border rounded-lg p-3">
                <div>
                  <div className="font-medium">{c.razon_social}</div>
                  <div className="text-sm text-slate-500">{c.cuit} · {c.condicion_iva}</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`inline-block w-3 h-3 rounded-full ${
                    c.semaforo === "verde" ? "bg-green-500" :
                    c.semaforo === "amarillo" ? "bg-yellow-500" : "bg-red-500"
                  }`} />
                  <span className="text-xs text-slate-500 capitalize">{c.semaforo}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="bg-white rounded-xl shadow-md p-6">
        <h2 className="font-semibold text-slate-800 mb-4">Vencimientos próximos</h2>
        {data.vencimientos_proximos.length === 0 ? (
          <p className="text-sm text-slate-400">Sin vencimientos en los próximos 30 días.</p>
        ) : (
          <ul className="space-y-2">
            {data.vencimientos_proximos.map((v, i) => (
              <li key={i} className="flex justify-between text-sm border-b last:border-0 py-2">
                <span>{v.impuesto}</span>
                <span className="text-slate-500">{v.fecha}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {data.alertas.length > 0 && (
        <section className="bg-white rounded-xl shadow-md p-6">
          <h2 className="font-semibold text-slate-800 mb-4">Alertas</h2>
          <div className="space-y-2">
            {data.alertas.map((a, i) => (
              <div key={i} className={`rounded-lg p-3 text-sm ${
                a.nivel === "critical" ? "bg-red-100 text-red-700" :
                a.nivel === "warning" ? "bg-yellow-100 text-yellow-700" :
                "bg-blue-100 text-blue-700"
              }`}>
                {a.mensaje}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
