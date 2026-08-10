import { useState } from "react"
import { login } from "../api"
import { useTheme } from "./ui/theme-provider"
import { Moon, Sun, Building2 } from "lucide-react"

export default function Login({ onLogin }: { onLogin: (token: string) => void }) {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [cargando, setCargando] = useState(false)
  const { isDark, toggle } = useTheme()

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
    <div className="min-h-screen flex items-center justify-center bg-surface-canvas">
      {/* Theme toggle floating */}
      <button
        onClick={toggle}
        className="fixed top-4 right-4 p-2 rounded-lg hover:bg-muted transition-colors"
        aria-label={isDark ? "Modo claro" : "Modo oscuro"}
      >
        {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
      </button>

      <div className="w-full max-w-[400px] px-6">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center">
            <Building2 className="w-5 h-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-foreground">Estudio Contable</h1>
            <p className="text-sm text-muted-foreground">Gestión fiscal integral</p>
          </div>
        </div>

        <form onSubmit={enviar} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Usuario</label>
            <input
              className="w-full h-10 px-3 rounded-md border border-input bg-background text-foreground text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-0 transition-colors"
              placeholder="owner"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Contraseña</label>
            <input
              className="w-full h-10 px-3 rounded-md border border-input bg-background text-foreground text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-0 transition-colors"
              type="password"
              placeholder="••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {error && (
            <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          <button
            type="submit"
            className="w-full h-10 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 active:bg-primary/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={cargando}
          >
            {cargando ? "Ingresando…" : "Ingresar"}
          </button>
        </form>

        <p className="mt-6 text-xs text-center text-muted-foreground">
          Demo: owner/owner123 · senior/senior123
        </p>
      </div>
    </div>
  )
}
