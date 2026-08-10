import { useState } from "react"
import AppLayout, { type Solapa } from "../components/AppLayout"
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
    <AppLayout activeTab={solapa} onTabChange={setSolapa} onLogout={handleLogout}>
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
    </AppLayout>
  )
}
