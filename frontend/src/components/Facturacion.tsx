import { useEffect, useState } from "react"
import { emitirFactura, listarClientes, type Cliente } from "../api"

const TIPOS_COMPROBANTE = [
  { valor: "FACTURA_A", etiqueta: "Factura A" },
  { valor: "FACTURA_B", etiqueta: "Factura B" },
  { valor: "FACTURA_C", etiqueta: "Factura C" },
  { valor: "FACTURA_M", etiqueta: "Factura M" },
  { valor: "NOTA_CREDITO_A", etiqueta: "Nota de Crédito A" },
  { valor: "NOTA_CREDITO_B", etiqueta: "Nota de Crédito B" },
  { valor: "NOTA_CREDITO_C", etiqueta: "Nota de Crédito C" },
  { valor: "NOTA_DEBITO_A", etiqueta: "Nota de Débito A" },
  { valor: "NOTA_DEBITO_B", etiqueta: "Nota de Débito B" },
  { valor: "NOTA_DEBITO_C", etiqueta: "Nota de Débito C" },
] as const

const CONDICIONES = [
  { valor: "RI", etiqueta: "Responsable Inscripto" },
  { valor: "MT", etiqueta: "Monotributo" },
  { valor: "EX", etiqueta: "Exento" },
  { valor: "CF", etiqueta: "Consumidor Final" },
] as const

export default function Facturacion({ token }: { token: string }) {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [clienteId, setClienteId] = useState<number | "">("")

  const [tipo, setTipo] = useState("FACTURA_B")
  const [puntoVenta, setPuntoVenta] = useState(1)
  const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 10))
  const [receptorCuit, setReceptorCuit] = useState("")
  const [receptorRazon, setReceptorRazon] = useState("")
  const [receptorCondicion, setReceptorCondicion] = useState("RI")
  const [neto, setNeto] = useState("")
  const [alicuota, setAlicuota] = useState("0.21")
  const [total, setTotal] = useState("")

  const [error, setError] = useState("")
  const [cargando, setCargando] = useState(false)
  const [resultado, setResultado] = useState<{
    cae: string
    vencimiento_cae: string
    numero: number
    tipo: string
    punto_venta: number
    total: string
    pdf_base64: string
  } | null>(null)

  async function cargarClientes() {
    try {
      setClientes(await listarClientes(token))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar clientes")
    }
  }

  useEffect(() => {
    cargarClientes()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const n = parseFloat(neto.replace(",", "."))
    const a = parseFloat(alicuota)
    if (!isNaN(n) && !isNaN(a)) {
      setTotal((n * (1 + a)).toFixed(2))
    }
  }, [neto, alicuota])

  async function handleEmitir(e: React.FormEvent) {
    e.preventDefault()
    if (!clienteId) {
      setError("Seleccioná un cliente emisor")
      return
    }
    setCargando(true)
    setError("")
    setResultado(null)
    try {
      const res = await emitirFactura(
        Number(clienteId),
        {
          tipo,
          punto_venta: puntoVenta,
          numero: 0,
          fecha,
          receptor_cuit: receptorCuit,
          receptor_razon: receptorRazon,
          receptor_condicion: receptorCondicion,
          neto: neto.replace(",", "."),
          alicuota,
          total: total.replace(",", "."),
        },
        token,
      )
      setResultado(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al emitir")
    } finally {
      setCargando(false)
    }
  }

  function descargarPdf() {
    if (!resultado) return
    const bytes = new Uint8Array(
      resultado.pdf_base64.match(/.{1,2}/g)!.map((b) => parseInt(b, 16)),
    )
    const blob = new Blob([bytes], { type: "application/pdf" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `FACTURA_${resultado.numero}_${resultado.cae}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <form
        onSubmit={handleEmitir}
        className="bg-white rounded-xl shadow-md p-6 space-y-4"
      >
        <h2 className="font-semibold text-slate-800">Emitir factura electrónica</h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="sm:col-span-2">
            <label className="block text-sm text-slate-500 mb-1">Cliente emisor</label>
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
          </div>

          <div>
            <label className="block text-sm text-slate-500 mb-1">Tipo</label>
            <select
              className="border rounded-lg px-3 py-2 w-full"
              value={tipo}
              onChange={(e) => setTipo(e.target.value)}
            >
              {TIPOS_COMPROBANTE.map((t) => (
                <option key={t.valor} value={t.valor}>
                  {t.etiqueta}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-slate-500 mb-1">Punto de venta</label>
            <input
              type="number"
              className="border rounded-lg px-3 py-2 w-full"
              value={puntoVenta}
              onChange={(e) => setPuntoVenta(Number(e.target.value))}
            />
          </div>

          <div>
            <label className="block text-sm text-slate-500 mb-1">Fecha</label>
            <input
              type="date"
              className="border rounded-lg px-3 py-2 w-full"
              value={fecha}
              onChange={(e) => setFecha(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm text-slate-500 mb-1">CUIT receptor</label>
            <input
              className="border rounded-lg px-3 py-2 w-full"
              placeholder="20-27396523-9"
              value={receptorCuit}
              onChange={(e) => setReceptorCuit(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm text-slate-500 mb-1">Razón social receptor</label>
            <input
              className="border rounded-lg px-3 py-2 w-full"
              placeholder="Razón social"
              value={receptorRazon}
              onChange={(e) => setReceptorRazon(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm text-slate-500 mb-1">Condición IVA receptor</label>
            <select
              className="border rounded-lg px-3 py-2 w-full"
              value={receptorCondicion}
              onChange={(e) => setReceptorCondicion(e.target.value)}
            >
              {CONDICIONES.map((c) => (
                <option key={c.valor} value={c.valor}>
                  {c.etiqueta}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-slate-500 mb-1">Neto ($)</label>
            <input
              type="number"
              step="0.01"
              className="border rounded-lg px-3 py-2 w-full"
              placeholder="10000"
              value={neto}
              onChange={(e) => setNeto(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm text-slate-500 mb-1">Alícuota IVA</label>
            <select
              className="border rounded-lg px-3 py-2 w-full"
              value={alicuota}
              onChange={(e) => setAlicuota(e.target.value)}
            >
              <option value="0.21">21 %</option>
              <option value="0.105">10,5 %</option>
              <option value="0.27">27 %</option>
              <option value="0">0 %</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-slate-500 mb-1">Total ($)</label>
            <input
              type="number"
              step="0.01"
              className="border rounded-lg px-3 py-2 w-full bg-slate-50"
              value={total}
              readOnly
            />
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          className="bg-slate-800 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
          disabled={cargando}
        >
          {cargando ? "Emitiendo…" : "Emitir factura"}
        </button>
      </form>

      {resultado && (
        <div className="bg-white rounded-xl shadow-md p-6 space-y-3 border-l-4 border-green-500">
          <h3 className="font-semibold text-green-700">✓ Factura aprobada por ARCA</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="text-slate-500">CAE</div>
            <div className="font-mono">{resultado.cae}</div>
            <div className="text-slate-500">Número</div>
            <div>{resultado.numero}</div>
            <div className="text-slate-500">Vencimiento CAE</div>
            <div>{resultado.vencimiento_cae}</div>
            <div className="text-slate-500">Total</div>
            <div>${resultado.total}</div>
          </div>
          <button
            onClick={descargarPdf}
            className="bg-green-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-green-700"
          >
            Descargar PDF
          </button>
        </div>
      )}
    </div>
  )
}
