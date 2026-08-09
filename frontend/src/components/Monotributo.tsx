import { useEffect, useState } from "react"
import { consultarMonotributo, listarClientes, type Cliente } from "../api"

interface MonotributoData {
  categoria_actual: string
  categoria_proyectada: string
  ingresos_acumulados: string
  techo_actual: string
  porcentaje_del_techo: number
  alerta: { nivel: string; mensaje: string } | null
  cuota_mensual: string | null
}

export default function Monotributo({ token }: { token: string }) {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [clienteId, setClienteId] = useState<number | "">("")
  const [data, setData] = useState<MonotributoData | null>(null)
  const [error, setError] = useState("")
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    listarClientes(token).then(setClientes).catch((e) => setError(e.message))
  }, [token])

  async function consultar() {
    if (!clienteId) return
    setCargando(true)
    setError("")
    try {
      const res = await consultarMonotributo(Number(clienteId), token)
      setData(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error")
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-md p-6 space-y-4">
        <h2 className="font-semibold text-slate-800">Monotributo</h2>
        <div className="flex gap-3">
          <select
            className="border rounded-lg px-3 py-2 flex-1"
            value={clienteId}
            onChange={(e) => setClienteId(Number(e.target.value) || "")}
          >
            <option value="">Seleccionar cliente…</option>
            {clientes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.razon_social} — {c.cuit}
              </option>
            ))}
          </select>
          <button
            onClick={consultar}
            disabled={cargando || !clienteId}
            className="bg-slate-800 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {cargando ? "Consultando…" : "Consultar"}
          </button>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>

      {data && (
        <div className="bg-white rounded-xl shadow-md p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="text-slate-500">Categoría actual</div>
            <div className="font-semibold">{data.categoria_actual}</div>
            <div className="text-slate-500">Categoría proyectada</div>
            <div className="font-semibold">{data.categoria_proyectada}</div>
            <div className="text-slate-500">Ingresos acumulados</div>
            <div>${Number(data.ingresos_acumulados).toLocaleString("es-AR")}</div>
            <div className="text-slate-500">Techo actual</div>
            <div>${Number(data.techo_actual).toLocaleString("es-AR")}</div>
            <div className="text-slate-500">% del techo</div>
            <div className="font-semibold">{data.porcentaje_del_techo}%</div>
            <div className="text-slate-500">Cuota mensual</div>
            <div>${data.cuota_mensual ? Number(data.cuota_mensual).toLocaleString("es-AR") : "—"}</div>
          </div>

          {data.alerta && (
            <div className={`rounded-lg p-3 text-sm ${
              data.alerta.nivel === "critical"
                ? "bg-red-100 text-red-700"
                : "bg-yellow-100 text-yellow-700"
            }`}>
              {data.alerta.mensaje}
            </div>
          )}

          <div className="w-full bg-slate-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all ${
                data.porcentaje_del_techo >= 95
                  ? "bg-red-500"
                  : data.porcentaje_del_techo >= 80
                  ? "bg-yellow-500"
                  : "bg-green-500"
              }`}
              style={{ width: `${Math.min(data.porcentaje_del_techo, 100)}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
