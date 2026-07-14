# Guia de demo tecnica

## Objetivo de la practica

Demostrar mecanismos de tolerancia a fallas en una arquitectura simplificada de reservas de entradas desplegada en Kubernetes.

## Arquitectura implementada

- `gateway`: entrada del sistema y rate limiting.
- `reservations`: orquestador de la reserva.
- `inventory`: control de asientos con PostgreSQL y bloqueo transaccional.
- `payments`: pasarela simulada con latencia/fallos configurables.
- `notifications`: servicio no critico con fallback.
- `postgres`: persistencia del inventario.

## Mecanismos defendidos en vivo

| Escenario | Falla inyectada | Defensa implementada | Evidencia esperada |
| --- | --- | --- | --- |
| Inventario Fantasma | `inventory` en 0 replicas | retry con backoff y fallo controlado | HTTP 503/504 sin confirmar reserva |
| Pasarela Lenta | pagos con 20 s de latencia | timeout y circuit breaker | varios 503 y breaker `open` |
| Correo Perdido | `notifications` en 0 replicas | fallback no critico | reserva `confirmed` con notificacion `pending` |
| Diluvio de Peticiones | muchas reservas seguidas | rate limiting en gateway | respuestas HTTP 429 |

## Escenarios para analisis teorico

| Escenario | Riesgo | Tratamiento recomendado |
| --- | --- | --- |
| Base de Datos Intermitente | perdida temporal de conectividad o indisponibilidad de escritura | health checks, readiness probes, retry con backoff, replicas administradas, backups y failover |
| Condicion de Carrera | dos usuarios reservan el mismo asiento al mismo tiempo | transacciones ACID, `SELECT FOR UPDATE`, idempotencia y pruebas concurrentes |

## Flujo recomendado de ejecucion

1. Preparar cluster con al menos 2 nodos:

```powershell
.\scripts\00-minikube-ensure-two-nodes.ps1
```

Captura: `kubectl get nodes -o wide`.

2. Construir y cargar imagenes:

```powershell
.\scripts\01-build-load-images.ps1
```

Captura: terminal mostrando imagenes construidas/cargadas.

3. Desplegar en Kubernetes:

```powershell
.\scripts\02-deploy-k8s.ps1
```

Captura: `kubectl -n ticket-lab get pods -o wide`.

4. Abrir port-forward:

```powershell
.\scripts\03-port-forward.ps1
```

Nota: si se reinicia un deployment usado por port-forward, ejecuta `.\scripts\13-stop-port-forward.ps1` y luego `.\scripts\03-port-forward.ps1`.

5. Evidencia base:

```powershell
.\scripts\04-baseline-evidence.ps1
```

6. Escenario 1, Inventory down:

```powershell
.\scripts\05-chaos-inventory-down.ps1
.\scripts\06-recover-inventory.ps1
```

7. Escenario 2, Payments lento:

```powershell
.\scripts\07-chaos-payments-slow.ps1
.\scripts\08-recover-payments.ps1
```

8. Escenario 3, Notifications caido:

```powershell
.\scripts\09-chaos-notifications-down.ps1
.\scripts\10-recover-notifications.ps1
```

9. Escenario 4, diluvio de peticiones:

```powershell
.\scripts\11-chaos-traffic-spike.ps1
```

10. Reiniciar laboratorio si se necesita repetir:

```powershell
.\scripts\12-reset-lab.ps1
```

11. Detener port-forward al finalizar:

```powershell
.\scripts\13-stop-port-forward.ps1
```

## Capturas minimas para el informe

1. Cluster con 2 nodos.
2. Pods y servicios desplegados en `ticket-lab`.
3. Health checks e inventario inicial.
4. Reserva confirmada en escenario normal.
5. Inventory down con respuesta controlada.
6. Payments lento con circuit breaker abierto.
7. Notifications down con reserva confirmada y notificacion pendiente.
8. Traffic spike con respuestas 429.
