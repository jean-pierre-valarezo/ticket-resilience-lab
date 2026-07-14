# Evidence

Guardar aqui capturas, logs y salidas relevantes para el informe y la demo.

Capturas iniciales recomendadas:

1. Servicios levantados con `docker compose up --build`.
2. Health check del gateway.
3. Inventario inicial con asientos disponibles.
4. Reserva exitosa desde el gateway.
5. Inventario posterior mostrando el asiento reservado.

Capturas Kubernetes recomendadas:

1. `kubectl get nodes -o wide` con minimo 2 nodos.
2. `kubectl -n ticket-lab get pods -o wide`.
3. `kubectl -n ticket-lab get svc`.
4. `04-baseline-evidence.ps1` con health checks, inventario y reserva.
5. `05-chaos-inventory-down.ps1` mostrando `inventory` en 0 replicas y respuesta 503/504.
6. `07-chaos-payments-slow.ps1` mostrando timeouts y circuit breaker abierto.
7. `09-chaos-notifications-down.ps1` mostrando reserva confirmada con notificacion pendiente.
8. `11-chaos-traffic-spike.ps1` mostrando respuestas 429.

Usar nombres descriptivos, por ejemplo:

- `01-compose-servicios-levantados.png`
- `02-health-gateway.png`
- `03-inventario-inicial.png`
- `04-reserva-exitosa.png`
- `05-inventario-asiento-reservado.png`
- `06-k8s-dos-nodos.png`
- `07-k8s-pods-ticket-lab.png`
- `08-chaos-inventory-down.png`
- `09-chaos-payments-circuit-breaker.png`
- `10-chaos-notifications-fallback.png`
- `11-chaos-traffic-rate-limit.png`
