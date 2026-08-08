export interface CampoExtraido {
  valor: string | number
  confianza: number
  fuente: "qr" | "ocr" | "llm"
}

export interface ResultadoExtraccion {
  estado: "ok" | "revisar"
  campos: Record<string, CampoExtraido>
}

export interface Cliente {
  id: number
  cuit: string
  razon_social: string
  condicion_iva: "RI" | "MT" | "EX" | "CF"
}

export interface LiquidacionIva {
  periodo: string
  debito: Record<string, string>
  credito: Record<string, string>
  saldo_favor_anterior: string
  saldo_a_pagar: string
  saldo_a_favor_final: string
  comprobantes_incluidos: number[]
}

async function manejarError(r: Response): Promise<never> {
  if (r.status === 401) throw new Error("Sesión vencida: volvé a ingresar")
  if (r.status === 422) throw new Error("Datos inválidos (revisá CUIT, condición IVA o alícuotas)")
  if (r.status === 409) throw new Error("Ese CUIT ya está registrado")
  if (r.status === 404) throw new Error("Cliente no encontrado")
  throw new Error(`Error del servidor (${r.status})`)
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

function conToken(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` }
}

export async function subirComprobante(
  archivo: File,
  token: string
): Promise<ResultadoExtraccion> {
  const form = new FormData()
  form.append("archivo", archivo)
  const r = await fetch("/extraccion/comprobante", {
    method: "POST",
    headers: conToken(token),
    body: form,
  })
  if (!r.ok) await manejarError(r)
  return r.json()
}

export async function listarClientes(token: string): Promise<Cliente[]> {
  const r = await fetch("/clientes", { headers: conToken(token) })
  if (!r.ok) await manejarError(r)
  return r.json()
}

export async function crearCliente(
  datos: Omit<Cliente, "id">,
  token: string
): Promise<Cliente> {
  const r = await fetch("/clientes", {
    method: "POST",
    headers: { ...conToken(token), "Content-Type": "application/json" },
    body: JSON.stringify(datos),
  })
  if (!r.ok) await manejarError(r)
  return r.json()
}

export async function confirmarComprobante(
  clienteId: number,
  datos: {
    tipo: "venta" | "compra"
    fecha: string
    lineas: { alicuota: string; neto: string; iva: string }[]
  },
  token: string
): Promise<void> {
  const r = await fetch(`/clientes/${clienteId}/comprobantes`, {
    method: "POST",
    headers: { ...conToken(token), "Content-Type": "application/json" },
    body: JSON.stringify(datos),
  })
  if (!r.ok) await manejarError(r)
}

export async function liquidacionIva(
  clienteId: number,
  periodo: string,
  token: string
): Promise<LiquidacionIva> {
  const r = await fetch(`/clientes/${clienteId}/iva/${periodo}`, {
    headers: conToken(token),
  })
  if (!r.ok) await manejarError(r)
  return r.json()
}
