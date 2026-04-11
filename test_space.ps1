# PowerShell script to test HuggingFace Space endpoints
# Run this after your Space is awake and responding

$BaseURL = "https://kalletlamadhav-sql-optimized-env-new.hf.space"
$Timeout = 30

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "  TESTING HUGGINGFACE SPACE ENDPOINTS" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Base URL: $BaseURL"
Write-Host "Timeout: $Timeout seconds"
Write-Host ""

# Test 1: Health
Write-Host "`n[TEST 1] GET /health" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BaseURL/health" -UseBasicParsing -TimeoutSec $Timeout
    $json = $response.Content | ConvertFrom-Json
    Write-Host $response.Content -ForegroundColor Green
    
    if ($json.status -eq "ok") {
        Write-Host "✅ PASS: Health check OK" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL: Status is not 'ok'" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ FAIL: $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# Test 2: Tasks
Write-Host "`n[TEST 2] GET /tasks" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BaseURL/tasks" -UseBasicParsing -TimeoutSec $Timeout
    $json = $response.Content | ConvertFrom-Json
    Write-Host $response.Content.Substring(0, [Math]::Min(500, $response.Content.Length)) -ForegroundColor Green
    
    if ($json.Count -ge 3) {
        Write-Host "✅ PASS: Found $($json.Count) tasks" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL: Expected 3+ tasks, got $($json.Count)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ FAIL: $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# Test 3: Reset
Write-Host "`n[TEST 3] POST /reset?task_id=gst_missing_index" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BaseURL/reset?task_id=gst_missing_index" -Method POST -UseBasicParsing -TimeoutSec $Timeout
    $json = $response.Content | ConvertFrom-Json
    Write-Host $response.Content.Substring(0, [Math]::Min(500, $response.Content.Length)) -ForegroundColor Green
    
    if ($json.task_id -eq "gst_missing_index") {
        Write-Host "✅ PASS: Reset to gst_missing_index" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL: Expected gst_missing_index, got $($json.task_id)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ FAIL: $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# Test 4: State
Write-Host "`n[TEST 4] GET /state" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BaseURL/state" -UseBasicParsing -TimeoutSec $Timeout
    $json = $response.Content | ConvertFrom-Json
    Write-Host $response.Content -ForegroundColor Green
    
    if ($json.current_task_id) {
        Write-Host "✅ PASS: State returned" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL: Invalid state" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ FAIL: $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# Test 5: Step (CRITICAL - Reward Validation)
Write-Host "`n[TEST 5] POST /step (REWARD VALIDATION)" -ForegroundColor Yellow
try {
    $body = @{
        optimized_query = "SELECT gstin_supplier, invoice_date FROM gst_invoice_records WHERE invoice_date >= '2025-01-01'"
        identified_pattern = "MISSING_INDEX"
        explanation = "Added index on invoice_date to avoid full table scan"
        index_statements = @("CREATE INDEX idx_invoice_date ON gst_invoice_records(invoice_date)")
        schema_analysis = "No index on invoice_date"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$BaseURL/step" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec $Timeout
    $json = $response.Content | ConvertFrom-Json
    Write-Host $response.Content.Substring(0, [Math]::Min(800, $response.Content.Length)) -ForegroundColor Green
    
    # Extract reward value
    $reward = $json.reward
    if ($reward -is [PSCustomObject]) {
        $rewardValue = $reward.total
    } else {
        $rewardValue = $reward
    }
    
    Write-Host "`n💰 REWARD: $rewardValue" -ForegroundColor Cyan
    Write-Host "   Type: $($rewardValue.GetType().Name)" -ForegroundColor Cyan
    
    # Validate reward
    if ($rewardValue -eq 0.0) {
        Write-Host "❌ FAIL: Reward is exactly 0.0 (FORBIDDEN)" -ForegroundColor Red
    } elseif ($rewardValue -eq 1.0) {
        Write-Host "❌ FAIL: Reward is exactly 1.0 (FORBIDDEN)" -ForegroundColor Red
    } elseif ($rewardValue -le 0.01) {
        Write-Host "❌ FAIL: Reward $rewardValue is <= 0.01" -ForegroundColor Red
    } elseif ($rewardValue -ge 0.99) {
        Write-Host "❌ FAIL: Reward $rewardValue is >= 0.99" -ForegroundColor Red
    } elseif (($rewardValue -gt 0.01) -and ($rewardValue -lt 0.99)) {
        Write-Host "✅ PASS: Reward $rewardValue is strictly between 0.01 and 0.99 ✓" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL: Reward $rewardValue is invalid" -ForegroundColor Red
    }
    
    # Check other fields
    if ($json.done -is [bool]) {
        Write-Host "✅ 'done' field present: $($json.done)" -ForegroundColor Green
    } else {
        Write-Host "❌ 'done' field missing or invalid" -ForegroundColor Red
    }
    
    if ($json.observation) {
        Write-Host "✅ 'observation' field present" -ForegroundColor Green
    } else {
        Write-Host "❌ 'observation' field missing" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ FAIL: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "  TEST COMPLETE" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
