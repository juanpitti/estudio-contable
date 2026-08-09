import { useState } from "react"
import { consultarAsistente } from "../api"

interface Mensaje {
  rol: "user" | "asistente"
  texto: string
  fuente?: string
  links?: { label: string; path: string }[]
}

export default function Asistente({ token }: { token: string }) {
  const [mensajes, setMensajes] = useState<Mensaje[]>([
    { rol: "asistente", texto: "Hola, soy tu asistente contable. Preguntame sobre tus clientes, vencimientos o alertas." },
  ])
  const [input, setInput] = useState("")
  const [cargando, setCargando] = useState(false)

  async function enviar() {
    if (!input.trim()) return
    const pregunta = input.trim()
    setMensajes((m) => [...m, { rol: "user", texto: pregunta }])
    setInput("")
    setCargando(true)

    try {
      const res = await consultarAsistente(pregunta, token)
      setMensajes((m) => [
        ...m,
        { rol: "asistente", texto: res.texto, fuente: res.fuente, links: res.links },
      ])
    } catch (e) {
      setMensajes((m) => [
        ...m,
        { rol: "asistente", texto: e instanceof Error ? e.message : "Error" },
      ])
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-md p-6 space-y-4">
      <h2 className="font-semibold text-slate-800">Asistente Contable</h2>
      <p className="text-xs text-slate-400">Solo consulta datos del sistema. No asesora normativamente.</p>

      <div className="space-y-3 max-h-96 overflow-y-auto border rounded-lg p-3 bg-slate-50">
        {mensajes.map((m, i) => (
          <div key={i} className={`flex ${m.rol === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
              m.rol === "user"
                ? "bg-slate-800 text-white"
                : "bg-white border text-slate-800"
            }`}>
              <p>{m.texto}</p>
              {m.fuente && (
                <p className="text-xs text-slate-400 mt-1">Fuente: {m.fuente}</p>
              )}
              {m.links && m.links.length > 0 && (
                <div className="flex gap-2 mt-2">
                  {m.links.map((l, j) => (
                    <span key={j} className="text-xs text-blue-600 underline">{l.label}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {cargando && (
          <div className="flex justify-start">
            <div className="bg-white border rounded-lg px-3 py-2 text-sm text-slate-500">Pensando…</div>
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          className="border rounded-lg px-3 py-2 flex-1 text-sm"
          placeholder="Ej: ¿qué clientes tienen la IVA sin revisar?"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && enviar()}
        />
        <button
          onClick={enviar}
          disabled={cargando}
          className="bg-slate-800 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          Enviar
        </button>
      </div>
    </div>
  )
}
