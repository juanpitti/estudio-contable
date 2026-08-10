# Design Brief — Estudio Contable (AR)

## Product Identity
Plataforma web de gestión para estudios contables argentinos. Módulos: cartera de clientes, ingesta de comprobantes IVA, liquidación mensual, facturación con CAE, F.931, convenio multilateral, monotributo, conciliación bancaria, monitor fiscal y asistente IA.

## Primary User
**Operator (contador/a del estudio)** — usa la app diariamente para:
- Revisar semáforos de clientes y vencimientos fiscales
- Ingresar y conciliar comprobantes
- Emitir facturas con CAE
- Generar F.931 y liquidaciones
- Monitorear alertas fiscales

Secondary: **Owner** (socio del estudio) — revisa dashboards, gestiona usuarios.

## Design Intent
Profesional, confiable, sin ruido. La información fiscal es densa por naturaleza; el diseño debe reducir la carga cognitiva, no aumentarla. Prioridad: claridad > velocidad > belleza.

## Principles (ranked)
1. **Claridad fiscal primero** — números legibles, estados explícitos, sin adornos que compitan por atención
2. **Confianza visual** — colores sobrios, tipografía estable, sin gradientes ni efectos que eviten "app de trading/crypto"
3. **Accesibilidad mínima WCAG AA** — contraste 4.5:1 en todo texto, navegación por teclado, `prefers-reduced-motion`
4. **Densidad adaptable** — vistas de lista densas (tablas), vistas de detalle aireadas (formularios)
5. **Consistencia de patrones** — mismo tratamiento visual para mismos conceptos fiscales en todos los módulos

## Success Metric
Un contador puede navegar de login a la liquidación IVA de un cliente en ≤4 clicks sin perderse.

## Out of Scope
- Marketing site / landing (la app es el producto)
- Onboarding interactivo (usuarios capacitados por el estudio)
- Personalización visual por cliente (monocromático fijo)

## Constraints
- Stack: React 19 + Tailwind CSS + shadcn/ui
- Dark mode obligatorio (uso en horarios extendidos)
- Mobile: lectura/view-only; acciones complejas en desktop
- Locale: español (AR) — separador decimal coma, fecha DD/MM/YYYY

## Signature Bet
**Tabulación tipográfica en números fiscales** — toda cifra monetaria usa `tabular-nums` + alineación derecha + monoespaciado. Es una señal visual sutil que comunica "esto es serio" y mejora la legibilidad de columnas de montos.

## Accent Color Rationale
Verde esmeralda (hue ~155° OKLCH) — asociación cultural con finanzas, saldo positivo, "en regla". Evita el azul genérico de SaaS. Saturación contenida para no competir con los semáforos de estado (verde/amarillo/rojo).

## Learned Constraints
(none yet — populated via `/remember`)
