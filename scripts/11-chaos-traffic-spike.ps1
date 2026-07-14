param(
    [string]$GatewayUrl = "http://localhost:8080",
    [int]$Requests = 25
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. "$PSScriptRoot/lib/http.ps1"

Write-Host "Inyectando falla: diluvio de peticiones contra el gateway."
Write-Host "Se esperan respuestas 429 cuando el rate limiter corta el exceso de trafico."

$results = @()
for ($i = 1; $i -le $Requests; $i++) {
    $body = @{
        event_id = "concert-1"
        seat_id = "A10"
        user_id = "flood-demo-$i"
        amount = 50
    }

    $result = Invoke-JsonPost -Uri "$GatewayUrl/reserve" -Body $body
    $results += [pscustomobject]@{
        Attempt = $i
        StatusCode = $result.StatusCode
        Body = $result.Body
    }

    Write-Host ("Intento {0}: HTTP {1}" -f $i, $result.StatusCode)
}

Write-Host ""
Write-Host "Resumen por codigo HTTP:"
$results | Group-Object StatusCode | Select-Object Name, Count | Format-Table -AutoSize

Write-Host ""
Write-Host "Captura recomendada: resumen donde aparezcan respuestas HTTP 429."
