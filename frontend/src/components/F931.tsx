import { useEffect, useState } from "react"
import { generarF931, listarClientes, type Cliente } from "../api"

interface Empleado {
  cuit: string
  apellido_nombre: string
  remuneracion: string
  aportes: string
  contribuciones: string
  situacion_revista: string
}

export default function F931({ token }: { token: string }) {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [clienteId, setClienteId] = useState<number | "">("")
  const [periodo, setPeriodo] = useState("202608")
  const [empleados, setEmpleados] = useState<Empleado[]>([
    { cuit: "", apellido_nombre: "", remuneracion: "", aportes: "", contribuciones: "", situacion_revista: "1" },
  ])
  const [error, setError] = useState("")
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    listarClientes(token).then(setClientes).catch((e) => setError(e.message))
  }, [token])

  function actualizarEmpleado(idx: number, campo: keyof Empleado, valor: string) {
    const nuevos = [...empleados]
    nuevos[idx][campo] = valor
    setEmpleados(nuevos)
  }

  function agregarEmpleado() {
    setEmpleados([...empleados, { cuit: "", apellido_nombre: "", remuneracion: "", aportes: "", contribuciones: "", situacion_revista: "1" }])
  }

  async function generar() {
    if (!clienteId) return
    setCargando(true)
    setError("")
    try {
      const res = await generarF931(Number(clienteId), { periodo, empleados }, token)
      const blob = new Blob([res.txt], { type: "text/plain" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = res.nombre_archivo
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error")
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-md p-6 space-y-4">
        <h2 className="font-semibold text-slate-800">Generar F.931</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <select
            className="border rounded-lg px-3 py-2"
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
          <input
            className="border rounded-lg px-3 py-2"
            placeholder="Período (AAAAMM)"
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value)}
          />
        </div>

        {empleados.map((emp, idx) => (
          <div key={idx} className="grid grid-cols-1 sm:grid-cols-6 gap-2 text-sm">
            <input className="border rounded px-2 py-1" placeholder="CUIT" value={emp.cuit} onChange={(e) => actualizarEmpleado(idx, "cuit", e.target.value)} />
            <input className="border rounded px-2 py-1" placeholder="Apellido y nombre" value={emp.apellido_nombre} onChange={(e) => actualizarEmpleado(idx, "apellido_nombre", e.target.value)} />
            <input className="border rounded px-2 py-1" placeholder="Remuneración" value={emp.remuneracion} onChange={(e) => actualizarEmpleado(idx, "remuneracion", e.target.value)} />
            <input className="border rounded px-2 py-1" placeholder="Aportes" value={emp.aportes} onChange={(e) => actualizarEmpleado(idx, "aportes", e.target.value)} />
            <input className="border rounded px-2 py-1" placeholder="Contribuciones" value={emp.contribuciones} onChange={(e) => actualizarEmpleado(idx, "contribuciones", e.target.value)} />
            <input className="border rounded px-2 py-1" placeholder="Situación" value={emp.situacion_revista} onChange={(e) => actualizarEmpleado(idx, "situacion_revista", e.target.value)} />
          </div>
        ))}

        <button onClick={agregarEmpleado} className="text-sm text-slate-600 hover:text-slate-800">
          + Agregar empleado
        </button>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          onClick={generar}
          disabled={cargando || !clienteId}
          className="bg-slate-800 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {cargando ? "Generando…" : "Descargar TXT F.931"}
        </button>
      </div>
    </div>
  )
}
