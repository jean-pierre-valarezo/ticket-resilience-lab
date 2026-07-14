function Convert-ResponseContent {
    param([string]$Content)

    if ([string]::IsNullOrWhiteSpace($Content)) {
        return $null
    }

    try {
        return $Content | ConvertFrom-Json
    }
    catch {
        return $Content
    }
}

function Read-ErrorResponseContent {
    param($Response)

    if ($null -eq $Response) {
        return ""
    }

    if ($Response -is [System.Net.HttpWebResponse]) {
        $stream = $Response.GetResponseStream()
        if ($null -eq $stream) {
            return ""
        }

        $reader = [System.IO.StreamReader]::new($stream)
        try {
            return $reader.ReadToEnd()
        }
        finally {
            $reader.Dispose()
        }
    }

    if ($Response.Content) {
        return $Response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    }

    return ""
}

function Invoke-JsonGet {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Uri
    )

    try {
        $response = Invoke-WebRequest -Uri $Uri -Method Get -UseBasicParsing
        return [pscustomobject]@{
            StatusCode = [int]$response.StatusCode
            Body = Convert-ResponseContent -Content $response.Content
        }
    }
    catch {
        $statusCode = 0
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }

        $content = Read-ErrorResponseContent -Response $_.Exception.Response
        return [pscustomobject]@{
            StatusCode = $statusCode
            Body = Convert-ResponseContent -Content $content
        }
    }
}

function Invoke-JsonPost {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Uri,

        [Parameter(Mandatory = $true)]
        [object]$Body
    )

    $json = $Body | ConvertTo-Json -Depth 10

    try {
        $response = Invoke-WebRequest -Uri $Uri -Method Post -ContentType "application/json" -Body $json -UseBasicParsing
        return [pscustomobject]@{
            StatusCode = [int]$response.StatusCode
            Body = Convert-ResponseContent -Content $response.Content
        }
    }
    catch {
        $statusCode = 0
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }

        $content = Read-ErrorResponseContent -Response $_.Exception.Response
        return [pscustomobject]@{
            StatusCode = $statusCode
            Body = Convert-ResponseContent -Content $content
        }
    }
}

function Write-JsonResult {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,

        [Parameter(Mandatory = $true)]
        [object]$Result
    )

    Write-Host ""
    Write-Host "=== $Title ==="
    Write-Host "HTTP $($Result.StatusCode)"
    $Result.Body | ConvertTo-Json -Depth 10
}
