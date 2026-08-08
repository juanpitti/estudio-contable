import { useState } from "react"
import Login from "../components/Login"
import SubirFactura from "../components/SubirFactura"

export default function Home() {
  const [token, setToken] = useState<string>(() => localStorage.getItem("token") ?? "")

  function handleLogin(nuevoToken: string) {
    localStorage.setItem("token", nuevoToken)
    setToken(nuevoToken)
  }

  function handleLogout() {
    localStorage.removeItem("token")
    setToken("")
  }

  return token ? (
    <SubirFactura token={token} onLogout={handleLogout} />
  ) : (
    <Login onLogin={handleLogin} />
  )
}
