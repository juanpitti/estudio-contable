import { useEffect, useState } from "react"
import { generarCM05, listarClientes, type Cliente } from "../api"

export default function Convenio({ token }: { token: string }) {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [clienteId, setClienteId] = useState<number | "">("")
  const [ingresos, setIngresos] = useState<Record<string, string>>({
    "01": "", "02": "", "04": "", "13": "", "21": "",
  })
  const [resultado, setResultado] = useState<{
    total_ingresos: string
    atribuciones: Record<string, { ingreso: string; porcentaje: string }>
    coeficientes: Record<string, string>
  } | null>(null)
  const [error, setError] = useState("")
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    listarClientes(token).then(setClientes).catch((e) => setError(e.message))
  }, [token])

  const PROVINCIAS = [
    { codigo: "01", nombre: "CABA" },
    { codigo: "02", nombre: "Buenos Aires" },
    { codigo: "03", nombre: "Catamarca" },
    { codigo: "04", nombre: "Córdoba" },
    { codigo: "05", nombre: "Corrientes" },
    { codigo: "06", nombre: "Chaco" },
    { codigo: "07", nombre: "Chubut" },
    { codigo: "08", nombre: "Entre Ríos" },
    { codigo: "09", nombre: "Formosa" },
    { codigo: "10", nombre: "Jujuy" },
    { codigo: "11", nombre: "La Pampa" },
    { codigo: "12", nombre: "La Rioja" },
    { codigo: "13", nombre: "Mendoza" },
    { codigo: "14", nombre: "Misiones" },
    { codigo: "15", nombre: "Neuquén" },
    { codigo: "16", nombre: "Río Negro" },
    { codigo: "17", nombre: "Salta" },
    { codigo: "18", nombre: "San Juan" },
    { codigo: "19", nombre: "San Luis" },
    { codigo: "20", nombre: "Santa Cruz" },
    { codigo: "21", nombre: "Santa Fe" },
    { codigo: "22", nombre: "Santiago del Estero" },
    { codigo: "23", nombre: "Tucumán" },
    { codigo: "24", nombre: "Tierra del Fuego" },
  ]

  async function calcular() {
    if (!clienteId) return
    setCargando(true)
    setError("")
    try {
      const filtrados = Object.fromEntries(
        Object.entries(ingresos).filter(([, v]) => v !== "")
      )
      const res = await generarCM05(Number(clienteId), filtrados, token)
      setResultado(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error")
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-md p-6 space-y-4">
        <h2 className="font-semibold text-slate-800">Convenio Multilateral — CM05</h2>
        <select
          className="border rounded-lg px-3 py-2 w-full"
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

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {PROVINCIAS.map((p) => (
            <div key={p.codigo} className="flex items-center gap-2">
              <label className="text-sm text-slate-500 w-32">{p.nombre}</label>
              <input
                type="number"
                className="border rounded-lg px-2 py-1 text-sm flex-1"
                placeholder="Ingresos"
                value={ingresos[p.codigo] || ""}
                onChange={(e) => setIngresos({ ...ingresos, [p.codigo]: e.target.value })}
              />
            </div>
          ))}
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          onClick={calcular}
          disabled={cargando || !clienteId}
          className="bg-slate-800 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {cargando ? "Calculando…" : "Calcular atribución"}
        </button>
      </div>

      {resultado && (
        <div className="bg-white rounded-xl shadow-md p-6 space-y-4">
          <h3 className="font-semibold text-slate-800">Resultado</h3>
          <p className="text-sm text-slate-500">Total ingresos: <span className="font-semibold text-slate-800">${Number(resultado.total_ingresos).toLocaleString("es-AR")}</span></p>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b">
                <th className="py-2">Jurisdicción</th>
                <th>Ingreso</th>
                <th>%</th>
                <th>Coeficiente</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(resultado.atribuciones).map(([codigo, a]) => (
                <tr key={codigo} className="border-b last:border-0">
                  <td className="py-2">{PROVINCIAS.find((p) => p.codigo === codigo)?.nombre || codigo}</td>
                  <td>${Number(a.ingreso).toLocaleString("es-AR")}</td>
                  <td>{a.porcentaje}%</td>
                  <td>{resultado.coeficientes[codigo] || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
