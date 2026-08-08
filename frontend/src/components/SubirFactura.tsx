import { useCallback, useState } from "react"
import { subirComprobante, type ResultadoExtraccion } from "../api"

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

export default function SubirFactura({
  token,
  onLogout,
}: {
  token: string
  onLogout: () => void
}) {
  const [arrastrando, setArrastrando] = useState(false)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState("")
  const [resultado, setResultado] = useState<ResultadoExtraccion | null>(null)
  const [nombreArchivo, setNombreArchivo] = useState("")

  const procesar = useCallback(
    async (archivo: File) => {
      setCargando(true)
      setError("")
      setResultado(null)
      setNombreArchivo(archivo.name)
      try {
        setResultado(await subirComprobante(archivo, token))
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error al procesar")
      } finally {
        setCargando(false)
      }
    },
    [token]
  )

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-white shadow-sm">
        <div className="max-w-3xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-slate-800">Subir factura</h1>
          <button onClick={onLogout} className="text-sm text-slate-500 hover:text-slate-800">
            Cerrar sesión
          </button>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8 space-y-6">
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
          </section>
        )}
      </main>
    </div>
  )
}
