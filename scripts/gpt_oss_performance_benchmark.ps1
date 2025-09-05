# GPT-OSS 性能基準測試腳本 (PowerShell版本)
# 用於Windows環境的Docker容器性能測試

param(
    [string]$ContainerName = "gpt-oss-benchmark",
    [string]$ImageName = "tradingagents:gpt-oss",
    [int]$Port = 8080,
    [string]$TestResultsDir = "./benchmark_results"
)

# 顏色定義
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    Cyan = "Cyan"
}

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Test-ServiceHealth {
    param([string]$Url)
    try {
        $response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 10
        return $true
    }
    catch {
        return $false
    }
}

function Measure-ResponseTime {
    param([string]$Url)
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 30 | Out-Null
        $stopwatch.Stop()
        return $stopwatch.Elapsed.TotalSeconds
    }
    catch {
        $stopwatch.Stop()
        return -1
    }
}

# 初始化
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultsFile = Join-Path $TestResultsDir "benchmark_$timestamp.json"

# 創建結果目錄
if (!(Test-Path $TestResultsDir)) {
    New-Item -ItemType Directory -Path $TestResultsDir -Force | Out-Null
}

Write-ColorOutput "=== GPT-OSS 性能基準測試 (PowerShell版) ===" $Colors.Blue
Write-ColorOutput "測試時間: $(Get-Date)" $Colors.Cyan
Write-ColorOutput "映像名稱: $ImageName" $Colors.Cyan
Write-ColorOutput "結果文件: $resultsFile" $Colors.Cyan
Write-ColorOutput ""

# 初始化結果對象
$results = @{
    test_timestamp = (Get-Date).ToString("o")
    image_name = $ImageName
    platform = "Windows PowerShell"
    tests = @{}
}

# 清理函數
function Cleanup {
    Write-ColorOutput "清理測試環境..." $Colors.Yellow
    try {
        docker stop $ContainerName 2>$null | Out-Null
        docker rm $ContainerName 2>$null | Out-Null
    }
    catch {
        # 忽略清理錯誤
    }
}

# 設置清理
trap { Cleanup; break }

try {
    # 測試1: 容器啟動時間
    Write-ColorOutput "測試1: 容器啟動時間" $Colors.Blue
    $startTime = Get-Date
    
    # 啟動容器
    $dockerCmd = "docker run -d --name $ContainerName --gpus all -p ${Port}:${Port} $ImageName"
    Invoke-Expression $dockerCmd | Out-Null
    
    # 等待服務就緒
    Write-ColorOutput "等待服務啟動..." $Colors.Cyan
    $maxWait = 120
    $waitCount = 0
    $serviceUrl = "http://localhost:$Port/health"
    
    do {
        Start-Sleep -Seconds 1
        $waitCount++
        if ($waitCount % 10 -eq 0) {
            Write-ColorOutput "等待中... ${waitCount}s" $Colors.Cyan
        }
    } while (!(Test-ServiceHealth $serviceUrl) -and $waitCount -lt $maxWait)
    
    if ($waitCount -ge $maxWait) {
        throw "服務啟動超時"
    }
    
    $endTime = Get-Date
    $startupTime = ($endTime - $startTime).TotalSeconds
    
    Write-ColorOutput "✓ 容器啟動時間: $([math]::Round($startupTime, 2))秒" $Colors.Green
    $results.tests.startup_time = $startupTime
    
    # 測試2: 健康檢查響應時間
    Write-ColorOutput "測試2: 健康檢查響應時間" $Colors.Blue
    $healthTimes = @()
    
    for ($i = 1; $i -le 5; $i++) {
        $responseTime = Measure-ResponseTime $serviceUrl
        if ($responseTime -gt 0) {
            $healthTimes += $responseTime
            Write-ColorOutput "健康檢查 $i : $([math]::Round($responseTime, 3))秒" $Colors.Cyan
        }
    }
    
    if ($healthTimes.Count -gt 0) {
        $avgHealthTime = ($healthTimes | Measure-Object -Average).Average
        Write-ColorOutput "✓ 平均健康檢查響應時間: $([math]::Round($avgHealthTime, 3))秒" $Colors.Green
        $results.tests.avg_health_response_time = $avgHealthTime
    }
    
    # 測試3: GPU檢測和記憶體狀態
    Write-ColorOutput "測試3: GPU檢測和記憶體狀態" $Colors.Blue
    try {
        $healthResponse = Invoke-RestMethod -Uri $serviceUrl -Method Get
        Write-ColorOutput "GPU可用性: $($healthResponse.cuda_available)" $Colors.Cyan
        
        $memoryUrl = "http://localhost:$Port/memory"
        $memoryResponse = Invoke-RestMethod -Uri $memoryUrl -Method Get
        Write-ColorOutput "記憶體狀態: 已獲取" $Colors.Green
        $results.tests.memory_status = $memoryResponse
    }
    catch {
        Write-ColorOutput "⚠ 無法獲取GPU/記憶體狀態" $Colors.Yellow
    }
    
    # 測試4: 推理性能測試
    Write-ColorOutput "測試4: 推理性能測試" $Colors.Blue
    $testMessages = @(
        @{message="簡單測試"; max_tokens=20; description="簡單測試"},
        @{message="分析AAPL股票的技術面和基本面"; max_tokens=50; description="金融分析測試"},
        @{message="請詳細分析當前市場情緒和投資建議"; max_tokens=100; description="複雜分析測試"}
    )
    
    $inferenceTimes = @()
    $chatUrl = "http://localhost:$Port/chat"
    
    for ($i = 0; $i -lt $testMessages.Count; $i++) {
        $test = $testMessages[$i]
        Write-ColorOutput "推理測試 $($i+1): $($test.description)" $Colors.Cyan
        
        try {
            $body = $test | ConvertTo-Json
            $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
            
            $response = Invoke-RestMethod -Uri $chatUrl -Method Post -Body $body -ContentType "application/json" -TimeoutSec 30
            
            $stopwatch.Stop()
            $inferenceTime = $stopwatch.Elapsed.TotalSeconds
            $inferenceTimes += $inferenceTime
            
            $tokensUsed = if ($response.tokens_used) { $response.tokens_used } else { "N/A" }
            Write-ColorOutput "  ✓ 推理時間: $([math]::Round($inferenceTime, 2))秒, 使用tokens: $tokensUsed" $Colors.Green
        }
        catch {
            Write-ColorOutput "  ✗ 推理測試失敗: $($_.Exception.Message)" $Colors.Red
        }
    }
    
    if ($inferenceTimes.Count -gt 0) {
        $avgInferenceTime = ($inferenceTimes | Measure-Object -Average).Average
        Write-ColorOutput "✓ 平均推理時間: $([math]::Round($avgInferenceTime, 2))秒" $Colors.Green
        $results.tests.avg_inference_time = $avgInferenceTime
    }
    
    # 測試5: 並發性能測試
    Write-ColorOutput "測試5: 並發性能測試" $Colors.Blue
    $concurrentRequests = 3
    Write-ColorOutput "執行 $concurrentRequests 個並發請求..." $Colors.Cyan
    
    $jobs = @()
    for ($i = 1; $i -le $concurrentRequests; $i++) {
        $job = Start-Job -ScriptBlock {
            param($Url, $Body)
            try {
                $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
                Invoke-RestMethod -Uri $Url -Method Post -Body $Body -ContentType "application/json" -TimeoutSec 30 | Out-Null
                $stopwatch.Stop()
                return $stopwatch.Elapsed.TotalSeconds
            }
            catch {
                return -1
            }
        } -ArgumentList $chatUrl, '{"message": "並發測試請求", "max_tokens": 50}'
        
        $jobs += $job
    }
    
    # 等待所有作業完成
    $jobs | Wait-Job | Out-Null
    $jobs | Remove-Job
    
    Write-ColorOutput "✓ 並發測試完成" $Colors.Green
    
    # 測試6: 資源使用情況
    Write-ColorOutput "測試6: 資源使用情況" $Colors.Blue
    try {
        $containerStats = docker stats $ContainerName --no-stream --format "table {{.CPUPerc}}`t{{.MemUsage}}`t{{.MemPerc}}"
        Write-ColorOutput "容器資源使用:" $Colors.Cyan
        Write-ColorOutput $containerStats $Colors.Cyan
    }
    catch {
        Write-ColorOutput "⚠ 無法獲取容器統計信息" $Colors.Yellow
    }
    
    # 測試7: 壓力測試
    Write-ColorOutput "測試7: 壓力測試 (10個快速請求)" $Colors.Blue
    $stressStartTime = Get-Date
    $stressSuccess = 0
    $stressTotal = 10
    
    for ($i = 1; $i -le $stressTotal; $i++) {
        try {
            $body = '{"message": "壓力測試", "max_tokens": 20}' | ConvertTo-Json
            Invoke-RestMethod -Uri $chatUrl -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10 | Out-Null
            $stressSuccess++
        }
        catch {
            # 忽略失敗的請求
        }
    }
    
    $stressEndTime = Get-Date
    $stressDuration = ($stressEndTime - $stressStartTime).TotalSeconds
    $successRate = [math]::Round(($stressSuccess * 100 / $stressTotal), 2)
    
    Write-ColorOutput "✓ 壓力測試完成: $stressSuccess/$stressTotal 成功 ($successRate%), 總時間: $([math]::Round($stressDuration, 2))秒" $Colors.Green
    
    $results.tests.stress_test = @{
        success_rate = $successRate
        duration = $stressDuration
    }
    
    # 生成測試報告
    Write-ColorOutput "" 
    Write-ColorOutput "=== 測試報告 ===" $Colors.Blue
    Write-ColorOutput "啟動時間: $([math]::Round($startupTime, 2))秒" $Colors.Cyan
    if ($avgHealthTime) {
        Write-ColorOutput "平均健康檢查響應時間: $([math]::Round($avgHealthTime, 3))秒" $Colors.Cyan
    }
    if ($avgInferenceTime) {
        Write-ColorOutput "平均推理時間: $([math]::Round($avgInferenceTime, 2))秒" $Colors.Cyan
    }
    Write-ColorOutput "壓力測試成功率: $successRate%" $Colors.Cyan
    
    # 性能評估
    Write-ColorOutput "" 
    Write-ColorOutput "=== 性能評估 ===" $Colors.Blue
    
    # 啟動時間評估
    if ($startupTime -lt 60) {
        Write-ColorOutput "✓ 啟動時間: 優秀 (<60秒)" $Colors.Green
    } elseif ($startupTime -lt 120) {
        Write-ColorOutput "⚠ 啟動時間: 良好 (<120秒)" $Colors.Yellow
    } else {
        Write-ColorOutput "✗ 啟動時間: 需要優化 (>120秒)" $Colors.Red
    }
    
    # 響應時間評估
    if ($avgHealthTime -and $avgHealthTime -lt 0.5) {
        Write-ColorOutput "✓ 響應時間: 優秀 (<0.5秒)" $Colors.Green
    } elseif ($avgHealthTime -and $avgHealthTime -lt 1.0) {
        Write-ColorOutput "⚠ 響應時間: 良好 (<1秒)" $Colors.Yellow
    } elseif ($avgHealthTime) {
        Write-ColorOutput "✗ 響應時間: 需要優化 (>1秒)" $Colors.Red
    }
    
    # 推理性能評估
    if ($avgInferenceTime -and $avgInferenceTime -lt 2.0) {
        Write-ColorOutput "✓ 推理性能: 優秀 (<2秒)" $Colors.Green
    } elseif ($avgInferenceTime -and $avgInferenceTime -lt 5.0) {
        Write-ColorOutput "⚠ 推理性能: 良好 (<5秒)" $Colors.Yellow
    } elseif ($avgInferenceTime) {
        Write-ColorOutput "✗ 推理性能: 需要優化 (>5秒)" $Colors.Red
    }
    
    # 穩定性評估
    if ($successRate -ge 95) {
        Write-ColorOutput "✓ 穩定性: 優秀 (≥95%)" $Colors.Green
    } elseif ($successRate -ge 90) {
        Write-ColorOutput "⚠ 穩定性: 良好 (≥90%)" $Colors.Yellow
    } else {
        Write-ColorOutput "✗ 穩定性: 需要優化 (<90%)" $Colors.Red
    }
    
    # 保存結果
    $results | ConvertTo-Json -Depth 10 | Out-File -FilePath $resultsFile -Encoding UTF8
    Write-ColorOutput ""
    Write-ColorOutput "測試完成！結果已保存到: $resultsFile" $Colors.Green
    
    # 生成HTML報告
    $htmlReport = $resultsFile -replace '\.json$', '.html'
    $htmlContent = @"
<!DOCTYPE html>
<html>
<head>
    <title>GPT-OSS 性能基準測試報告 (PowerShell版)</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .metric { margin: 10px 0; padding: 10px; border-left: 4px solid #007cba; }
        .good { border-left-color: #28a745; }
        .warning { border-left-color: #ffc107; }
        .error { border-left-color: #dc3545; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>GPT-OSS 性能基準測試報告 (PowerShell版)</h1>
        <p>測試時間: $(Get-Date)</p>
        <p>映像名稱: $ImageName</p>
        <p>平台: Windows PowerShell</p>
    </div>
    
    <h2>測試結果</h2>
    <table>
        <tr><th>測試項目</th><th>結果</th><th>評估</th></tr>
        <tr><td>容器啟動時間</td><td>$([math]::Round($startupTime, 2))秒</td><td>$(if($startupTime -lt 60){"優秀"}else{"需要優化"})</td></tr>
"@

    if ($avgHealthTime) {
        $htmlContent += "<tr><td>平均健康檢查響應時間</td><td>$([math]::Round($avgHealthTime, 3))秒</td><td>$(if($avgHealthTime -lt 0.5){"優秀"}else{"良好"})</td></tr>"
    }
    
    if ($avgInferenceTime) {
        $htmlContent += "<tr><td>平均推理時間</td><td>$([math]::Round($avgInferenceTime, 2))秒</td><td>$(if($avgInferenceTime -lt 2.0){"優秀"}else{"良好"})</td></tr>"
    }
    
    $htmlContent += @"
        <tr><td>壓力測試成功率</td><td>$successRate%</td><td>$(if($successRate -ge 95){"優秀"}else{"良好"})</td></tr>
    </table>
    
    <h2>詳細數據</h2>
    <pre>$($results | ConvertTo-Json -Depth 10)</pre>
</body>
</html>
"@
    
    $htmlContent | Out-File -FilePath $htmlReport -Encoding UTF8
    Write-ColorOutput "HTML報告已生成: $htmlReport" $Colors.Green
    
}
catch {
    Write-ColorOutput "測試過程中發生錯誤: $($_.Exception.Message)" $Colors.Red
    exit 1
}
finally {
    Cleanup
}

Write-ColorOutput ""
Write-ColorOutput "PowerShell版性能測試完成！" $Colors.Green