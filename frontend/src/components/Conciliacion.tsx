import { useEffect, useState } from "react"
import { importarConciliacion, listarClientes, type Cliente, type ResultadoConciliacion } from "../api"

const NIVEL_COLOR: Record<string, string> = {
  exacto: "bg-green-100 text-green-800",
  monto_fecha: "bg-blue-100 text-blue-800",
  monto_rango: "bg-amber-100 text-amber-800",
  aproximado: "bg-orange-100 text-orange-800",
}

export default function Conciliacion({ token }: { token: string }) {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [clienteId, setClienteId] = useState<number | "">("")
  const [delimitador, setDelimitador] = useState(";")
  const [resultado, setResultado] = useState<ResultadoConciliacion | null>(null)
  const [error, setError] = useState("")
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    listarClientes(token).then(setClientes).catch(() => {})
  }, [token])

  async function procesar(archivo: File) {
    if (clienteId === "") return
    setCargando(true)
    setError("")
    setResultado(null)
    try {
      setResultado(await importarConciliacion(clienteId, archivo, delimitador, token))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al procesar")
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-xl shadow-md p-6 space-y-3">
        <h2 className="font-semibold text-slate-800">Conciliación bancaria</h2>
        <div className="flex flex-wrap gap-3 items-end">
          <select
            className="border rounded-lg px-3 py-2"
            value={clienteId}
            onChange={(e) => setClienteId(e.target.value === "" ? "" : Number(e.target.value))}
          >
            <option value="">Elegí un cliente…</option>
            {clientes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.razon_social} ({c.cuit})
              </option>
            ))}
          </select>
          <select
            className="border rounded-lg px-3 py-2"
            value={delimitador}
            onChange={(e) => setDelimitador(e.target.value)}
          >
            <option value=";">Punto y coma (;)</option>
            <option value=",">Coma (,)</option>
            <option value="\t">Tab</option>
          </select>
          <label className="border-2 border-dashed border-slate-300 rounded-lg px-4 py-2 text-sm text-slate-600 cursor-pointer hover:bg-slate-50">
            <input
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) procesar(f)
              }}
            />
            {cargando ? "Procesando…" : "Subir CSV bancario"}
          </label>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </section>

      {resultado && (
        <section className="bg-white rounded-xl shadow-md p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-800">Resultado de conciliación</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-bold ${
              resultado.porcentaje_match >= 80 ? "bg-green-100 text-green-800" :
              resultado.porcentaje_match >= 50 ? "bg-amber-100 text-amber-800" :
              "bg-red-100 text-red-800"
            }`}>
              {resultado.porcentaje_match}% match
            </span>
          </div>

          {resultado.duplicados > 0 && (
            <p className="text-sm text-amber-700 bg-amber-50 rounded-lg p-3">
              ⚠️ Se detectaron {resultado.duplicados} movimiento(s) duplicado(s) en el archivo y fueron descartados.
            </p>
          )}

          {resultado.matches.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-500 mb-2">Matches encontrados</h4>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500 border-b">
                    <th className="py-2">Comp.</th>
                    <th>Mov.</th>
                    <th>Nivel</th>
                    <th>Monto comp.</th>
                    <th>Monto banco</th>
                  </tr>
                </thead>
                <tbody>
                  {resultado.matches.map((m, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="py-2">#{m.comprobante_id}</td>
                      <td>#{m.movimiento_id}</td>
                      <td>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${NIVEL_COLOR[m.nivel] || "bg-slate-100"}`}>
                          {m.nivel}
                        </span>
                      </td>
                      <td className="font-mono">${Number(m.monto_comprobante).toLocaleString("es-AR")}</td>
                      <td className="font-mono">${Number(m.monto_movimiento).toLocaleString("es-AR")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {resultado.diferencias.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-red-600 mb-2">Diferencias detectadas</h4>
              <ul className="text-sm space-y-1">
                {resultado.diferencias.map((d, i) => (
                  <li key={i} className="flex justify-between border-b py-1">
                    <span>Comp. #{d.comprobante_id} vs Mov. #{d.movimiento_id}</span>
                    <span className="font-mono text-red-600">
                      Dif: ${Number(d.monto_diferencia).toLocaleString("es-AR")}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {resultado.sin_match_banco.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-500 mb-2">Movimientos sin comprobante</h4>
              <ul className="text-sm space-y-1">
                {resultado.sin_match_banco.map((m) => (
                  <li key={m.id} className="flex justify-between border-b py-1">
                    <span>{m.fecha} — {m.descripcion}</span>
                    <span className="font-mono">${Number(m.monto).toLocaleString("es-AR")}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {resultado.sin_match_compras.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-500 mb-2">Comprobantes sin movimiento bancario</h4>
              <p className="text-sm text-slate-400">
                Comprobantes: #{resultado.sin_match_compras.join(", #")}
              </p>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
