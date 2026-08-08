import { useState } from "react"
import { login } from "../api"

export default function Login({ onLogin }: { onLogin: (token: string) => void }) {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [cargando, setCargando] = useState(false)

  async function enviar(e: React.FormEvent) {
    e.preventDefault()
    setCargando(true)
    setError("")
    try {
      onLogin(await login(username, password))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error de conexión")
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <form
        onSubmit={enviar}
        className="bg-white p-8 rounded-xl shadow-md w-full max-w-sm space-y-4"
      >
        <h1 className="text-2xl font-bold text-slate-800">Estudio Contable</h1>
        <p className="text-sm text-slate-500">Ingresá con tu usuario del estudio</p>
        <input
          className="w-full border rounded-lg px-3 py-2"
          placeholder="Usuario"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoFocus
        />
        <input
          className="w-full border rounded-lg px-3 py-2"
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          className="w-full bg-slate-800 text-white rounded-lg py-2 font-medium disabled:opacity-50"
          disabled={cargando}
        >
          {cargando ? "Ingresando…" : "Ingresar"}
        </button>
        <p className="text-xs text-slate-400">
          Demo: owner/owner123 · senior/senior123
        </p>
      </form>
    </div>
  )
}
