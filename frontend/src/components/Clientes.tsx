import { useEffect, useState } from "react"
import { crearCliente, listarClientes, type Cliente } from "../api"

const CONDICIONES = [
  { valor: "RI", etiqueta: "Responsable Inscripto" },
  { valor: "MT", etiqueta: "Monotributo" },
  { valor: "EX", etiqueta: "Exento" },
  { valor: "CF", etiqueta: "Consumidor Final" },
] as const

export default function Clientes({ token }: { token: string }) {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [cuit, setCuit] = useState("")
  const [razonSocial, setRazonSocial] = useState("")
  const [condicion, setCondicion] = useState<Cliente["condicion_iva"]>("RI")
  const [error, setError] = useState("")
  const [cargando, setCargando] = useState(false)

  async function cargar() {
    try {
      setClientes(await listarClientes(token))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar")
    }
  }

  useEffect(() => {
    cargar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function darDeAlta(e: React.FormEvent) {
    e.preventDefault()
    setCargando(true)
    setError("")
    try {
      await crearCliente(
        { cuit, razon_social: razonSocial, condicion_iva: condicion },
        token
      )
      setCuit("")
      setRazonSocial("")
      await cargar()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear")
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={darDeAlta} className="bg-white rounded-xl shadow-md p-6 space-y-3">
        <h2 className="font-semibold text-slate-800">Alta de cliente</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <input
            className="border rounded-lg px-3 py-2"
            placeholder="CUIT (20-27396523-9)"
            value={cuit}
            onChange={(e) => setCuit(e.target.value)}
          />
          <input
            className="border rounded-lg px-3 py-2"
            placeholder="Razón social"
            value={razonSocial}
            onChange={(e) => setRazonSocial(e.target.value)}
          />
          <select
            className="border rounded-lg px-3 py-2"
            value={condicion}
            onChange={(e) => setCondicion(e.target.value as Cliente["condicion_iva"])}
          >
            {CONDICIONES.map((c) => (
              <option key={c.valor} value={c.valor}>
                {c.etiqueta}
              </option>
            ))}
          </select>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          className="bg-slate-800 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
          disabled={cargando}
        >
          {cargando ? "Guardando…" : "Dar de alta"}
        </button>
      </form>

      <section className="bg-white rounded-xl shadow-md p-6">
        <h2 className="font-semibold text-slate-800 mb-3">Cartera</h2>
        {clientes.length === 0 ? (
          <p className="text-sm text-slate-400">Todavía no hay clientes cargados.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b">
                <th className="py-2">CUIT</th>
                <th>Razón social</th>
                <th>Condición IVA</th>
              </tr>
            </thead>
            <tbody>
              {clientes.map((c) => (
                <tr key={c.id} className="border-b last:border-0">
                  <td className="py-2 font-mono">{c.cuit}</td>
                  <td>{c.razon_social}</td>
                  <td>{CONDICIONES.find((x) => x.valor === c.condicion_iva)?.etiqueta}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  )
}
