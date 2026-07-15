.PHONY: local-up local-down k8s-setup k8s-deploy port-forward reset test-inventory test-payments test-notifications test-spike stop-forward

local-up:
	docker compose up --build -d

local-down:
	docker compose down

k8s-setup:
	powershell.exe -ExecutionPolicy Bypass -File .\scripts\00-minikube-ensure-two-nodes.ps1
	powershell.exe -ExecutionPolicy Bypass -File .\scripts\01-build-load-images.ps1

k8s-deploy:
	powershell.exe -ExecutionPolicy Bypass -File .\scripts\02-deploy-k8s.ps1

port-forward:
	powershell.exe -ExecutionPolicy Bypass -File .\scripts\03-port-forward.ps1

stop-forward:
	powershell.exe -ExecutionPolicy Bypass -File .\scripts\13-stop-port-forward.ps1

test-inventory:
	powershell.exe -ExecutionPolicy Bypass -File .\scripts\05-chaos-inventory-down.ps1
	@echo "Esperando observar el fallo HTTP 503..."
	@pause
	powershell.exe -ExecutionPolicy Bypass -File .\scripts\06-recover-inventory.ps1

test-payments:
	powershell.exe -ExecutionPolicy Bypass -File .\scripts\07-chaos-payments-slow.ps1
	@echo "Esperando observar Circuit Breaker Open..."
	@pause
	powershell.exe -ExecutionPolicy Bypass -File .\scripts\08-recover-payments.ps1

test-notifications:
	powershell.exe -ExecutionPolicy Bypass -File .\scripts\09-chaos-notifications-down.ps1
	@echo "Esperando observar Fallback (estado pending)..."
	@pause
	powershell.exe -ExecutionPolicy Bypass -File .\scripts\10-recover-notifications.ps1

test-spike:
	powershell.exe -ExecutionPolicy Bypass -File .\scripts\11-chaos-traffic-spike.ps1

reset:
	powershell.exe -ExecutionPolicy Bypass -File .\scripts\12-reset-lab.ps1
