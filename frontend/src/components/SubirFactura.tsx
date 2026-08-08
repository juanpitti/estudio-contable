import { useCallback, useEffect, useState } from "react"
import {
  confirmarComprobante,
  listarClientes,
  subirComprobante,
  type Cliente,
  type ResultadoExtraccion,
} from "../api"

const ETIQUETAS: Record<string, string> = {
  cuit: "CUIT emisor",
  pto_vta: "Punto de venta",
  tipo: "Tipo de comprobante",
  nro: "Número",
  fecha: "Fecha",
  importe: "Importe total",
  cae: "CAE",
}

function badge(confianza: number) {
  if (confianza >= 0.85)
    return <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800">Alta</span>
  if (confianza >= 0.5)
    return <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">Media</span>
  return <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800">Baja</span>
}

export default function SubirFactura({ token }: { token: string }) {
  const [arrastrando, setArrastrando] = useState(false)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState("")
  const [resultado, setResultado] = useState<ResultadoExtraccion | null>(null)
  const [nombreArchivo, setNombreArchivo] = useState("")

  // Confirmación humana (bitácora: el backend registra quién confirmó)
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [clienteId, setClienteId] = useState<number | "">("")
  const [tipo, setTipo] = useState<"venta" | "compra">("compra")
  const [fecha, setFecha] = useState("")
  const [neto, setNeto] = useState("")
  const [iva, setIva] = useState("")
  const [confirmado, setConfirmado] = useState(false)

  useEffect(() => {
    listarClientes(token).then(setClientes).catch(() => {})
  }, [token])

  const procesar = useCallback(
    async (archivo: File) => {
      setCargando(true)
      setError("")
      setResultado(null)
      setConfirmado(false)
      setNombreArchivo(archivo.name)
      try {
        const r = await subirComprobante(archivo, token)
        setResultado(r)
        if (r.campos["fecha"]) setFecha(String(r.campos["fecha"].valor))
        if (r.campos["importe"]) {
          const total = Number(r.campos["importe"].valor)
          const ivaSugerido = Math.round(((total * 21) / 121) * 100) / 100
          setIva(String(ivaSugerido))
          setNeto(String(Math.round((total - ivaSugerido) * 100) / 100))
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error al procesar")
      } finally {
        setCargando(false)
      }
    },
    [token]
  )

  async function confirmar() {
    if (clienteId === "") return
    setError("")
    try {
      await confirmarComprobante(
        clienteId,
        { tipo, fecha, lineas: [{ alicuota: "0.21", neto, iva }] },
        token
      )
      setConfirmado(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al confirmar")
    }
  }

  return (
    <div className="space-y-6">
      <label
        onDragOver={(e) => {
          e.preventDefault()
          setArrastrando(true)
        }}
        onDragLeave={() => setArrastrando(false)}
        onDrop={(e) => {
          e.preventDefault()
          setArrastrando(false)
          const f = e.dataTransfer.files?.[0]
          if (f) procesar(f)
        }}
        className={`block border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          arrastrando ? "border-slate-600 bg-slate-200" : "border-slate-300 bg-white"
        }`}
      >
        <input
          type="file"
          className="hidden"
          accept="image/*,.pdf"
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) procesar(f)
          }}
        />
        <p className="text-lg font-medium text-slate-700">
          {cargando ? "Procesando…" : "Arrastrá una foto, PDF o ticket acá"}
        </p>
        <p className="text-sm text-slate-400 mt-1">o hacé click para elegir el archivo</p>
      </label>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {resultado && (
        <section className="bg-white rounded-xl shadow-md p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-slate-800">{nombreArchivo}</h2>
            {resultado.estado === "ok" ? (
              <span className="px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800">
                Extracción OK
              </span>
            ) : (
              <span className="px-3 py-1 rounded-full text-sm font-semibold bg-amber-100 text-amber-800">
                REVISAR
              </span>
            )}
          </div>

          {resultado.estado === "revisar" && (
            <p className="text-sm text-amber-700 bg-amber-50 rounded-lg p-3">
              La confianza de algún campo es baja o el comprobante no se pudo leer.
              Revisá los datos manualmente antes de usarlos — el sistema no inventa valores.
            </p>
          )}

          {Object.keys(resultado.campos).length > 0 && (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b">
                  <th className="py-2">Campo</th>
                  <th>Valor</th>
                  <th>Confianza</th>
                  <th>Fuente</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(resultado.campos).map(([nombre, campo]) => (
                  <tr key={nombre} className="border-b last:border-0">
                    <td className="py-2 text-slate-600">{ETIQUETAS[nombre] ?? nombre}</td>
                    <td className="font-mono">{String(campo.valor)}</td>
                    <td>
                      {badge(campo.confianza)}{" "}
                      <span className="text-slate-400">{(campo.confianza * 100).toFixed(0)}%</span>
                    </td>
                    <td className="uppercase text-slate-500">{campo.fuente}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {resultado.estado === "ok" && !confirmado && (
            <div className="border-t pt-4 space-y-3">
              <h3 className="text-sm font-medium text-slate-700">
                Confirmar e ingresar a la cartera (queda en la bitácora a tu nombre)
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <select
                  className="border rounded-lg px-3 py-2 col-span-2 sm:col-span-1"
                  value={clienteId}
                  onChange={(e) => setClienteId(e.target.value === "" ? "" : Number(e.target.value))}
                >
                  <option value="">Cliente…</option>
                  {clientes.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.razon_social}
                    </option>
                  ))}
                </select>
                <select
                  className="border rounded-lg px-3 py-2"
                  value={tipo}
                  onChange={(e) => setTipo(e.target.value as "venta" | "compra")}
                >
                  <option value="compra">Compra</option>
                  <option value="venta">Venta</option>
                </select>
                <input
                  type="date"
                  className="border rounded-lg px-3 py-2"
                  value={fecha}
                  onChange={(e) => setFecha(e.target.value)}
                />
                <input
                  className="border rounded-lg px-3 py-2"
                  placeholder="Neto gravado 21%"
                  value={neto}
                  onChange={(e) => setNeto(e.target.value)}
                />
                <input
                  className="border rounded-lg px-3 py-2"
                  placeholder="IVA 21%"
                  value={iva}
                  onChange={(e) => setIva(e.target.value)}
                />
              </div>
              <button
                onClick={confirmar}
                disabled={clienteId === "" || !fecha || !neto || !iva}
                className="bg-green-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
              >
                Confirmar e ingresar
              </button>
            </div>
          )}

          {confirmado && (
            <p className="text-sm text-green-700 bg-green-50 rounded-lg p-3">
              ✓ Comprobante ingresado y registrado en la bitácora. Ya impacta en la liquidación
              del mes (solapa Liquidación).
            </p>
          )}
        </section>
      )}
    </div>
  )
}
