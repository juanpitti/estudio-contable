import { useEffect, useState } from "react"
import { liquidacionIva, listarClientes, type Cliente, type LiquidacionIva } from "../api"

const ETIQUETA_ALICUOTA: Record<string, string> = {
  "0.21": "21%",
  "0.105": "10.5%",
  "0.27": "27%",
}

function dinero(v: string): string {
  const n = Number(v)
  return n.toLocaleString("es-AR", { style: "currency", currency: "ARS" })
}

export default function Liquidacion({ token }: { token: string }) {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [clienteId, setClienteId] = useState<number | "">("")
  const [periodo, setPeriodo] = useState(() => new Date().toISOString().slice(0, 7))
  const [liq, setLiq] = useState<LiquidacionIva | null>(null)
  const [error, setError] = useState("")
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    listarClientes(token).then(setClientes).catch(() => {})
  }, [token])

  async function calcular() {
    if (clienteId === "") return
    setCargando(true)
    setError("")
    try {
      setLiq(await liquidacionIva(clienteId, periodo, token))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al calcular")
      setLiq(null)
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-xl shadow-md p-6 space-y-3">
        <h2 className="font-semibold text-slate-800">Pre-liquidación de IVA</h2>
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
          <input
            type="month"
            className="border rounded-lg px-3 py-2"
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value)}
          />
          <button
            onClick={calcular}
            disabled={cargando || clienteId === ""}
            className="bg-slate-800 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {cargando ? "Calculando…" : "Calcular"}
          </button>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </section>

      {liq && (
        <section className="bg-white rounded-xl shadow-md p-6 space-y-4">
          <h3 className="font-semibold text-slate-800">
            {liq.periodo} — {liq.comprobantes_incluidos.length} comprobante(s) incluido(s)
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <h4 className="text-sm font-medium text-slate-500 mb-2">Débito fiscal (ventas)</h4>
              {Object.keys(liq.debito).length === 0 ? (
                <p className="text-sm text-slate-400">Sin ventas en el período</p>
              ) : (
                <ul className="text-sm space-y-1">
                  {Object.entries(liq.debito).map(([a, t]) => (
                    <li key={a} className="flex justify-between border-b py-1">
                      <span>Alícuota {ETIQUETA_ALICUOTA[a] ?? a}</span>
                      <span className="font-mono">{dinero(t)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <h4 className="text-sm font-medium text-slate-500 mb-2">Crédito fiscal (compras)</h4>
              {Object.keys(liq.credito).length === 0 ? (
                <p className="text-sm text-slate-400">Sin compras en el período</p>
              ) : (
                <ul className="text-sm space-y-1">
                  {Object.entries(liq.credito).map(([a, t]) => (
                    <li key={a} className="flex justify-between border-b py-1">
                      <span>Alícuota {ETIQUETA_ALICUOTA[a] ?? a}</span>
                      <span className="font-mono">{dinero(t)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
          <div className="border-t pt-3 space-y-1 text-sm">
            {liq.saldo_favor_anterior !== "0" && (
              <p className="flex justify-between">
                <span className="text-slate-500">Saldo a favor del período anterior</span>
                <span className="font-mono">− {dinero(liq.saldo_favor_anterior)}</span>
              </p>
            )}
            {Number(liq.saldo_a_pagar) > 0 ? (
              <p className="flex justify-between text-lg font-bold text-red-700">
                <span>A pagar</span>
                <span className="font-mono">{dinero(liq.saldo_a_pagar)}</span>
              </p>
            ) : (
              <p className="flex justify-between text-lg font-bold text-green-700">
                <span>Saldo a favor (IVA técnico, se arrastra)</span>
                <span className="font-mono">{dinero(liq.saldo_a_favor_final)}</span>
              </p>
            )}
          </div>
          <p className="text-xs text-slate-400">
            Comprobantes incluidos: #{liq.comprobantes_incluidos.join(", #") || "ninguno"} — cada
            número sale del desglose por alícuota.
          </p>
        </section>
      )}
    </div>
  )
}
