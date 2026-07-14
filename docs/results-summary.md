# Resumen de resultados validados

Fecha de validacion: 2026-07-14

## Cluster Kubernetes

- Perfil usado: `ticket-lab`.
- Nodos: `ticket-lab` y `ticket-lab-m02`.
- Estado observado: ambos nodos `Ready`.
- CNI usado: `kindnet`.

## Despliegue

Namespace: `ticket-lab`.

Componentes desplegados:

- `gateway`
- `reservations`
- `inventory`
- `payments`
- `notifications`
- `postgres`

Estado observado: todos los pods quedaron `1/1 Running`.

## Evidencia base

- `GET /health` en gateway: HTTP 200.
- `GET /health` en inventory: HTTP 200.
- Inventario inicial: asientos `A1` a `A10` disponibles.
- Reserva normal: HTTP 200, estado `confirmed`.
- Resultado: el asiento queda marcado como `reserved` y la notificacion como `sent`.

## Escenario 1: Inventario Fantasma

Falla inyectada:

- `deployment/inventory` escalado a 0 replicas.

Resultado observado:

- Intento de reserva: HTTP 503.

Interpretacion:

- El sistema no confirma reservas cuando no puede validar inventario.
- La defensa combina retry con backoff y fallo controlado.

## Escenario 2: Pasarela Lenta

Falla inyectada:

- `PAYMENT_DELAY_MS=20000` en `deployment/payments`.

Resultado observado:

- 4 intentos de reserva: HTTP 503.
- Endpoint `/resilience`: circuit breaker de pagos en estado `open`.
- `failure_count=3`.

Interpretacion:

- El servicio `reservations` no queda bloqueado esperando la pasarela.
- La defensa combina timeout y circuit breaker.

## Escenario 3: Correo Perdido

Falla inyectada:

- `deployment/notifications` escalado a 0 replicas.

Resultado observado:

- Reserva: HTTP 200.
- Estado de reserva: `confirmed`.
- Notificacion: `pending`.
- Motivo: `notification service unavailable`.

Interpretacion:

- La notificacion se trata como dependencia no critica.
- El sistema preserva la venta y difiere la notificacion.

## Escenario 4: Diluvio de Peticiones

Falla inyectada:

- 25 solicitudes seguidas contra `POST /reserve`.

Resultado observado:

- 12 respuestas HTTP 409 por conflicto de asiento ya ocupado.
- 13 respuestas HTTP 429 por rate limiting.

Interpretacion:

- El gateway limita el exceso de trafico.
- La aplicacion distingue errores de negocio (`409`) de proteccion ante sobrecarga (`429`).
