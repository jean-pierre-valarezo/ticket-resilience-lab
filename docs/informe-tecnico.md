# Ticket Resilience Lab

**Práctica: mecanismos de tolerancia a fallas en Kubernetes**

**Integrantes:** Alexander Chuquipoma y Jean Pierre Valarezo
**Repositorio:** https://github.com/jean-pierre-valarezo/ticket-resilience-lab.git

## Resumen

Este informe documenta una práctica de tolerancia a fallas aplicada a un sistema simplificado de reservas de entradas desplegado en Kubernetes. La solución conserva los seis componentes solicitados y ejecuta cuatro fallos reales sobre un cluster de dos nodos.

## Cumplimiento de rúbrica

- Cluster multi-nodo: perfil minikube `ticket-lab` con `ticket-lab` y `ticket-lab-m02`.
- Componente crítico replicado: `inventory` con 2 réplicas distribuidas por nodo.
- Cuatro fallos implementados: inventory down, payments lento, notifications down y traffic spike.
- Dos fallos analizados: base de datos intermitente y condición de carrera.

## Declaración IA

Se útilizo ChatGPT 5.5 como apoyo para organizacion, revision de rúbrica, depuracion de comandos y redacción técnica. La ejecución práctica y las capturas fueron realizadas por los integrantes.

## Referencias

- Brewer, E. A. (2012). CAP twelve years later: How the rules have changed. Computer, 45(2), 23-29. https://doi.org/10.1109/MC.2012.37
- Fowler, M. (2014). Circuit Breaker. https://martinfowler.com/bliki/CircuitBreaker.html
- Kubernetes. (2026). Deployments. https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- Kubernetes. (2026). Services, Load Balancing, and Networking. https://kubernetes.io/docs/concepts/services-networking/
- Kubernetes. (2026). Configure Liveness, Readiness and Startup Probes. https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
- Kubernetes. (2026). Pod Topology Spread Constraints. https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/
- Kubernetes. (2026). Horizontal Pod Autoscaling. https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- Nygard, M. T. (2018). Release It! Design and Deploy Production-Ready Software (2nd ed.). Pragmatic Bookshelf.
- PostgreSQL Global Development Group. (2026). Explicit Locking. https://www.postgresql.org/docs/current/explicit-locking.html
- PostgreSQL Global Development Group. (2026). SELECT. https://www.postgresql.org/docs/current/sql-select.html