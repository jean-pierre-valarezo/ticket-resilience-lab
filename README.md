# Ticket Resilience Lab

Sistema simplificado de reservas de entradas para experimentar tolerancia a fallas en servicios distribuidos.

## Componentes

- `gateway`: punto de entrada para clientes. Incluye rate limiting simple.
- `reservations`: servicio core de reservas. Coordina inventario, pagos y notificaciones.
- `inventory`: verifica y reserva asientos. Usa PostgreSQL y bloqueo transaccional.
- `payments`: servicio externo simulado. Puede inyectar latencia y fallos.
- `notifications`: servicio no critico simulado. Puede fallar sin cancelar la reserva.
- `postgres`: base de datos compartida para inventario.

## Mecanismos de resiliencia iniciales

- Retry con backoff hacia `inventory`.
- Timeout y circuit breaker hacia `payments`.
- Fallback no critico hacia `notifications`.
- Rate limiting en `gateway`.
- Bloqueo transaccional en `inventory` para evitar reservas dobles.

## Ejecutar localmente con Docker Compose

```powershell
docker compose up --build -d
```

En otra terminal:

```powershell
curl http://localhost:8000/health
curl http://localhost:8002/health
curl http://localhost:8002/inventory/concert-1
```

Crear una reserva:

```powershell
curl -X POST http://localhost:8000/reserve `
  -H "Content-Type: application/json" `
  -d "{\"event_id\":\"concert-1\",\"seat_id\":\"A1\",\"user_id\":\"alexander\",\"amount\":50}"
```

Consultar estado del circuit breaker de pagos:

```powershell
curl http://localhost:8001/resilience
```

Detener el entorno local:

```powershell
docker compose down
```

## Ejecutar en Kubernetes con minikube

La practica pide Kubernetes con minimo 2 nodos. El flujo recomendado usa un perfil aislado de `minikube` llamado `ticket-lab`:

```powershell
.\scripts\00-minikube-ensure-two-nodes.ps1
.\scripts\01-build-load-images.ps1
.\scripts\02-deploy-k8s.ps1
.\scripts\03-port-forward.ps1
.\scripts\04-baseline-evidence.ps1
```

Los port-forward quedan en:

- Gateway: `http://localhost:8080`
- Reservations: `http://localhost:8081`
- Inventory: `http://localhost:8082`

## Escenarios de caos implementados

Ejecutar cada escenario y luego su recuperacion cuando aplique:

```powershell
.\scripts\05-chaos-inventory-down.ps1
.\scripts\06-recover-inventory.ps1

.\scripts\07-chaos-payments-slow.ps1
.\scripts\08-recover-payments.ps1

.\scripts\09-chaos-notifications-down.ps1
.\scripts\10-recover-notifications.ps1

.\scripts\11-chaos-traffic-spike.ps1
```

Reiniciar todo el laboratorio:

```powershell
.\scripts\12-reset-lab.ps1
```

Detener los port-forward:

```powershell
.\scripts\13-stop-port-forward.ps1
```

