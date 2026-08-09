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

export interface AlertaIva {
  nivel: "info" | "warning" | "critical"
  codigo: string
  mensaje: string
}

export interface LiquidacionIva {
  periodo: string
  debito: Record<string, string>
  credito: Record<string, string>
  saldo_favor_anterior: string
  saldo_a_pagar: string
  saldo_a_favor_final: string
  comprobantes_incluidos: number[]
  alertas: AlertaIva[]
}

export interface ResultadoConciliacion {
  porcentaje_match: number
  matches: { comprobante_id: number; movimiento_id: number; nivel: string; monto_comprobante: string; monto_movimiento: string }[]
  sin_match_compras: number[]
  sin_match_banco: { id: number; fecha: string; descripcion: string; monto: string }[]
  diferencias: { comprobante_id: number; movimiento_id: number; monto_diferencia: string }[]
  duplicados: number
  importados: number
  periodo: string
}

async function manejarError(r: Response): Promise<never> {
  if (r.status === 401) throw new Error("Sesión vencida: volvé a ingresar")
  if (r.status === 422) throw new Error("Datos inválidos (revisá CUIT, condición IVA o alícuotas)")
  if (r.status === 409) throw new Error("Ese CUIT ya está registrado")
  if (r.status === 404) throw new Error("Cliente no encontrado")
  if (r.status >= 500)
    throw new Error("No hay conexión con el backend (uvicorn :8000). Levantalo con `npm run dev` que inicia ambos servidores.")
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

export async function descargarPapelTrabajo(
  clienteId: number,
  periodo: string,
  token: string,
): Promise<Blob> {
  const r = await fetch(`/clientes/${clienteId}/iva/${periodo}/papel-trabajo`, {
    headers: conToken(token),
  })
  if (!r.ok) throw new Error("Error al descargar papel de trabajo")
  return r.blob()
}

export async function emitirFactura(
  clienteId: number,
  datos: {
    tipo: string
    punto_venta: number
    numero: number
    fecha: string
    receptor_cuit: string
    receptor_razon: string
    receptor_condicion: string
    neto: string
    alicuota: string
    total: string
  },
  token: string,
): Promise<{
  cae: string
  vencimiento_cae: string
  numero: number
  tipo: string
  punto_venta: number
  total: string
  pdf_base64: string
}> {
  const r = await fetch(`/clientes/${clienteId}/facturacion/emitir`, {
    method: "POST",
    headers: { ...conToken(token), "Content-Type": "application/json" },
    body: JSON.stringify(datos),
  })
  if (!r.ok) await manejarError(r)
  return r.json()
}

export async function consultarMonotributo(
  clienteId: number,
  token: string,
): Promise<{
  categoria_actual: string
  categoria_proyectada: string
  ingresos_acumulados: string
  techo_actual: string
  porcentaje_del_techo: number
  alerta: { nivel: string; mensaje: string } | null
  cuota_mensual: string | null
}> {
  const r = await fetch(`/clientes/${clienteId}/monotributo`, {
    headers: conToken(token),
  })
  if (!r.ok) await manejarError(r)
  return r.json()
}

export async function importarConciliacion(
  clienteId: number,
  archivo: File,
  delimitador: string,
  token: string,
): Promise<ResultadoConciliacion> {
  const form = new FormData()
  form.append("archivo", archivo)
  form.append("delimitador", delimitador)
  const r = await fetch(`/clientes/${clienteId}/conciliacion/importar`, {
    method: "POST",
    headers: conToken(token),
    body: form,
  })
  if (!r.ok) {
    const msg = await r.text()
    throw new Error(msg || "Error al importar")
  }
  return r.json()
}
