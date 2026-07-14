param(
    [string]$Profile = "ticket-lab"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$services = @(
    "gateway",
    "reservations",
    "inventory",
    "payments",
    "notifications"
)

kubectl config use-context $Profile | Out-Null

foreach ($service in $services) {
    $image = "ticket-resilience-lab-$service`:latest"
    $path = "services/$service"

    Write-Host ""
    Write-Host "Construyendo $image desde $path..."
    docker build -t $image $path
}

if (Get-Command minikube -ErrorAction SilentlyContinue) {
    foreach ($service in $services) {
        $image = "ticket-resilience-lab-$service`:latest"
        Write-Host ""
        Write-Host "Cargando $image dentro de $Profile..."
        minikube -p $Profile image load $image
    }
}

Write-Host ""
Write-Host "Imagenes listas para Kubernetes."
