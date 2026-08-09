import { useState } from "react"
import Asistente from "../components/Asistente"
import Clientes from "../components/Clientes"
import Conciliacion from "../components/Conciliacion"
import Convenio from "../components/Convenio"
import Dashboard from "../components/Dashboard"
import F931 from "../components/F931"
import Facturacion from "../components/Facturacion"
import Liquidacion from "../components/Liquidacion"
import Login from "../components/Login"
import Monotributo from "../components/Monotributo"
import SubirFactura from "../components/SubirFactura"

type Solapa = "dashboard" | "subir" | "clientes" | "facturacion" | "monotributo" | "f931" | "convenio" | "liquidacion" | "conciliacion" | "asistente"

const SOLAPAS: { id: Solapa; etiqueta: string }[] = [
  { id: "dashboard", etiqueta: "Dashboard" },
  { id: "subir", etiqueta: "Subir factura" },
  { id: "clientes", etiqueta: "Clientes" },
  { id: "facturacion", etiqueta: "Facturación" },
  { id: "monotributo", etiqueta: "Monotributo" },
  { id: "f931", etiqueta: "F.931" },
  { id: "convenio", etiqueta: "Convenio" },
  { id: "liquidacion", etiqueta: "Liquidación IVA" },
  { id: "conciliacion", etiqueta: "Conciliación" },
  { id: "asistente", etiqueta: "Asistente" },
]

export default function Home() {
  const [token, setToken] = useState<string>(() => localStorage.getItem("token") ?? "")
  const [solapa, setSolapa] = useState<Solapa>("dashboard")

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
        <nav className="max-w-3xl mx-auto px-4 flex gap-1 pb-2 flex-wrap">
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
        {solapa === "dashboard" && <Dashboard token={token} />}
        {solapa === "subir" && <SubirFactura token={token} />}
        {solapa === "clientes" && <Clientes token={token} />}
        {solapa === "facturacion" && <Facturacion token={token} />}
        {solapa === "monotributo" && <Monotributo token={token} />}
        {solapa === "f931" && <F931 token={token} />}
        {solapa === "convenio" && <Convenio token={token} />}
        {solapa === "liquidacion" && <Liquidacion token={token} />}
        {solapa === "conciliacion" && <Conciliacion token={token} />}
        {solapa === "asistente" && <Asistente token={token} />}
      </main>
    </div>
  )
}
