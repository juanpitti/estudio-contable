import { useState } from "react"
import Clientes from "../components/Clientes"
import Liquidacion from "../components/Liquidacion"
import Login from "../components/Login"
import SubirFactura from "../components/SubirFactura"

type Solapa = "subir" | "clientes" | "liquidacion"

const SOLAPAS: { id: Solapa; etiqueta: string }[] = [
  { id: "subir", etiqueta: "Subir factura" },
  { id: "clientes", etiqueta: "Clientes" },
  { id: "liquidacion", etiqueta: "Liquidación IVA" },
]

export default function Home() {
  const [token, setToken] = useState<string>(() => localStorage.getItem("token") ?? "")
  const [solapa, setSolapa] = useState<Solapa>("subir")

  function handleLogin(nuevoToken: string) {
    localStorage.setItem("token", nuevoToken)
    setToken(nuevoToken)
  }

  function handleLogout() {
    localStorage.removeItem("token")
    setToken("")
  }

  if (!token) return <Login onLogin={handleLogin} />

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-white shadow-sm">
        <div className="max-w-3xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-slate-800">Estudio Contable</h1>
          <button onClick={handleLogout} className="text-sm text-slate-500 hover:text-slate-800">
            Cerrar sesión
          </button>
        </div>
        <nav className="max-w-3xl mx-auto px-4 flex gap-1 pb-2">
          {SOLAPAS.map((s) => (
            <button
              key={s.id}
              onClick={() => setSolapa(s.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                solapa === s.id
                  ? "bg-slate-800 text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {s.etiqueta}
            </button>
          ))}
        </nav>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        {solapa === "subir" && <SubirFactura token={token} />}
        {solapa === "clientes" && <Clientes token={token} />}
        {solapa === "liquidacion" && <Liquidacion token={token} />}
      </main>
    </div>
  )
}
