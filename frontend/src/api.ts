export interface CampoExtraido {
  valor: string | number
  confianza: number
  fuente: "qr" | "ocr" | "llm"
}

export interface ResultadoExtraccion {
  estado: "ok" | "revisar"
  campos: Record<string, CampoExtraido>
}

export async function login(username: string, password: string): Promise<string> {
  const r = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  })
  if (!r.ok) throw new Error("Credenciales inválidas")
  return (await r.json()).access_token
}

export async function subirComprobante(
  archivo: File,
  token: string
): Promise<ResultadoExtraccion> {
  const form = new FormData()
  form.append("archivo", archivo)
  const r = await fetch("/extraccion/comprobante", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  })
  if (r.status === 401) throw new Error("Sesión vencida: volvé a ingresar")
  if (!r.ok) throw new Error(`Error del servidor (${r.status})`)
  return r.json()
}
