# Manual test driver for the Task 4 gateway, using Invoke-RestMethod instead of

#
#   Run from this directory after starting:
#   examples\fake_primary.py   on :9200
#   examples\fake_secondary.py on :9300
#   app\main.py                on :8002
#
# Usage: powershell -File examples\try_gateway.ps1

function Invoke-Gateway {
    param(
        [string]$Token,
        [hashtable]$Body
    )
    try {
        $resp = Invoke-RestMethod -Uri http://127.0.0.1:8002/v1/chat/completions `
            -Method Post -Headers @{Authorization = "Bearer $Token"} `
            -ContentType "application/json" -Body ($Body | ConvertTo-Json -Depth 5)
        Write-Host "OK:" ($resp | ConvertTo-Json -Depth 5 -Compress)
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        $errorBody = $_.ErrorDetails.Message
        if (-not $errorBody) {
            $stream = $_.Exception.Response.GetResponseStream()
            $stream.Position = 0
            $errorBody = (New-Object System.IO.StreamReader($stream)).ReadToEnd()
        }
        Write-Host "HTTP $status`: $errorBody"
    }
}

Write-Host "`n--- normal successful completion ---"
Invoke-Gateway -Token "t1" -Body @{messages = @(@{role="user"; content="hi"}); max_tokens = 50}

Write-Host "`n--- exceed entire token budget in one request (expect 429) ---"
Invoke-Gateway -Token "t2" -Body @{messages = @(@{role="user"; content="hi"}); max_tokens = 9999999}

Write-Host "`n--- primary set to 429 -> should fail over to secondary ---"
Invoke-RestMethod -Uri http://127.0.0.1:9200/set_mode/429 -Method Post | Out-Null
Invoke-Gateway -Token "t3" -Body @{messages = @(@{role="user"; content="hi"}); max_tokens = 10}

Write-Host "`n--- primary set to timeout -> should fail over after ~3s ---"
Invoke-RestMethod -Uri http://127.0.0.1:9200/set_mode/timeout -Method Post | Out-Null
Invoke-Gateway -Token "t4" -Body @{messages = @(@{role="user"; content="hi"}); max_tokens = 10}

Write-Host "`n--- primary set to 500 -> should NOT fail over (expect 503) ---"
Invoke-RestMethod -Uri http://127.0.0.1:9200/set_mode/500 -Method Post | Out-Null
Invoke-Gateway -Token "t5" -Body @{messages = @(@{role="user"; content="hi"}); max_tokens = 10}

Invoke-RestMethod -Uri http://127.0.0.1:9200/set_mode/ok -Method Post | Out-Null
Write-Host "`n--- primary reset back to ok ---"
