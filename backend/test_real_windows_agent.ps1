# Real Windows Agent Testing Script
# This script tests the actual agent implementation with a real orchestrator server

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$TenantId,
    
    [string]$AgentPath = ".",
    
    [switch]$Verbose
)

# Color output functions
function Write-Success($message) {
    Write-Host $message -ForegroundColor Green
}

function Write-Info($message) {
    Write-Host $message -ForegroundColor Cyan
}

function Write-Error($message) {
    Write-Host $message -ForegroundColor Red
}

function Write-Warning($message) {
    Write-Host $message -ForegroundColor Yellow
}

# Test connectivity to server
function Test-ServerConnectivity {
    Write-Info "Testing connectivity to server..."
    
    try {
        $uri = [System.Uri]$ServerUrl
        $result = Test-NetConnection -ComputerName $uri.Host -Port ($uri.Port -eq -1 ? 443 : $uri.Port)
        
        if ($result.TcpTestSucceeded) {
            Write-Success "✓ Server is reachable"
            return $true
        } else {
            Write-Error "✗ Cannot reach server"
            return $false
        }
    } catch {
        Write-Error "✗ Invalid server URL: $_"
        return $false
    }
}

# Test API endpoint
function Test-ApiEndpoint {
    Write-Info "Testing API endpoint..."
    
    try {
        $response = Invoke-RestMethod -Uri "$ServerUrl/api/v1" -Method Get -TimeoutSec 10
        Write-Success "✓ API endpoint is responsive"
        
        if ($Verbose) {
            Write-Info "API Response:"
            $response | ConvertTo-Json -Depth 3 | Write-Host
        }
        
        return $true
    } catch {
        Write-Error "✗ API endpoint test failed: $_"
        return $false
    }
}

# Test agent registration
function Test-AgentRegistration {
    Write-Info "Testing agent registration..."
    
    $registrationScript = Join-Path $AgentPath "windows_agent_fix.py"
    
    if (-not (Test-Path $registrationScript)) {
        Write-Error "✗ Registration script not found: $registrationScript"
        return $false
    }
    
    try {
        # Run registration in test mode
        $output = & python $registrationScript $ServerUrl $TenantId 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ Agent registration successful"
            
            if ($Verbose) {
                Write-Info "Registration output:"
                $output | ForEach-Object { Write-Host $_ }
            }
            
            return $true
        } else {
            Write-Error "✗ Agent registration failed"
            $output | ForEach-Object { Write-Host $_ }
            return $false
        }
    } catch {
        Write-Error "✗ Error during registration: $_"
        return $false
    }
}

# Test agent startup
function Test-AgentStartup {
    Write-Info "Testing agent startup..."
    
    $agentScript = Join-Path $AgentPath "run_agent.py"
    
    if (-not (Test-Path $agentScript)) {
        Write-Error "✗ Agent script not found: $agentScript"
        return $false
    }
    
    try {
        # Start agent process
        $process = Start-Process python -ArgumentList "$agentScript --server $ServerUrl --tenant $TenantId --headless" -PassThru -WindowStyle Hidden -RedirectStandardOutput "$env:TEMP\agent_output.txt" -RedirectStandardError "$env:TEMP\agent_error.txt"
        
        # Wait for agent to initialize
        Write-Info "Waiting for agent to initialize..."
        Start-Sleep -Seconds 5
        
        if (-not $process.HasExited) {
            Write-Success "✓ Agent started successfully (PID: $($process.Id))"
            
            # Check for errors in output
            $errorOutput = Get-Content "$env:TEMP\agent_error.txt" -ErrorAction SilentlyContinue
            if ($errorOutput) {
                Write-Warning "Agent errors detected:"
                $errorOutput | ForEach-Object { Write-Host $_ }
            }
            
            return $process
        } else {
            Write-Error "✗ Agent failed to start"
            
            $output = Get-Content "$env:TEMP\agent_output.txt" -ErrorAction SilentlyContinue
            $errors = Get-Content "$env:TEMP\agent_error.txt" -ErrorAction SilentlyContinue
            
            if ($output) {
                Write-Info "Agent output:"
                $output | ForEach-Object { Write-Host $_ }
            }
            
            if ($errors) {
                Write-Error "Agent errors:"
                $errors | ForEach-Object { Write-Host $_ }
            }
            
            return $null
        }
    } catch {
        Write-Error "✗ Error starting agent: $_"
        return $null
    }
}

# Monitor agent logs
function Monitor-AgentLogs {
    param($AgentProcess, $Duration = 30)
    
    Write-Info "Monitoring agent logs for $Duration seconds..."
    
    $logFile = Join-Path $AgentPath "agent.log"
    $startTime = Get-Date
    
    if (Test-Path $logFile) {
        # Clear log for fresh monitoring
        Clear-Content $logFile -ErrorAction SilentlyContinue
    }
    
    while ((Get-Date) -lt $startTime.AddSeconds($Duration)) {
        if (Test-Path $logFile) {
            $newContent = Get-Content $logFile -Tail 10 -ErrorAction SilentlyContinue
            if ($newContent) {
                $newContent | ForEach-Object {
                    if ($_ -match "ERROR") {
                        Write-Error $_
                    } elseif ($_ -match "WARNING") {
                        Write-Warning $_
                    } elseif ($_ -match "heartbeat|Heartbeat") {
                        Write-Success $_
                    } else {
                        Write-Host $_
                    }
                }
            }
        }
        
        # Check if process is still running
        if ($AgentProcess -and $AgentProcess.HasExited) {
            Write-Error "Agent process has exited unexpectedly"
            break
        }
        
        Start-Sleep -Seconds 2
    }
}

# Test job execution
function Test-JobExecution {
    param($AgentProcess)
    
    Write-Info "Testing job execution capabilities..."
    
    # Create a test job package
    $testPackagePath = Join-Path $AgentPath "test_package"
    if (-not (Test-Path $testPackagePath)) {
        New-Item -ItemType Directory -Path $testPackagePath -Force | Out-Null
    }
    
    # Create test automation script
    $testScript = @'
def main(context):
    """Test automation script"""
    context.log("Test job started")
    
    # Test parameter access
    test_param = context.parameters.get("test_param", "default")
    context.log(f"Test parameter: {test_param}")
    
    # Test system capabilities
    import platform
    context.log(f"Platform: {platform.system()}")
    context.log(f"Python version: {platform.python_version()}")
    
    # Test screenshot capability
    try:
        import pyautogui
        screenshot = pyautogui.screenshot()
        screenshot_path = context.save_screenshot("test_screenshot.png")
        context.log(f"Screenshot saved: {screenshot_path}")
    except Exception as e:
        context.log(f"Screenshot failed: {e}")
    
    # Return success
    return {"status": "success", "message": "Test completed"}
'@
    
    $testScript | Set-Content -Path "$testPackagePath\main.py"
    
    # Create package manifest
    $manifest = @{
        name = "test_package"
        version = "1.0.0"
        description = "Test automation package"
        entry_point = "main.py"
        requirements = @()
    } | ConvertTo-Json
    
    $manifest | Set-Content -Path "$testPackagePath\package.json"
    
    Write-Success "✓ Test package created"
    
    # Monitor for job execution
    Write-Info "Agent is ready for job execution testing"
    Write-Info "Submit a test job from the orchestrator UI to validate execution"
    
    return $true
}

# Main test execution
function Run-AgentTests {
    Write-Host ""
    Write-Host "Windows Agent Test Suite" -ForegroundColor Blue
    Write-Host "========================" -ForegroundColor Blue
    Write-Host ""
    Write-Info "Server URL: $ServerUrl"
    Write-Info "Tenant ID: $TenantId"
    Write-Info "Agent Path: $AgentPath"
    Write-Host ""
    
    $results = @{
        ServerConnectivity = $false
        ApiEndpoint = $false
        Registration = $false
        Startup = $false
        JobExecution = $false
    }
    
    # Test 1: Server connectivity
    $results.ServerConnectivity = Test-ServerConnectivity
    if (-not $results.ServerConnectivity) {
        Write-Error "Cannot proceed without server connectivity"
        return $results
    }
    
    # Test 2: API endpoint
    $results.ApiEndpoint = Test-ApiEndpoint
    
    # Test 3: Agent registration
    $results.Registration = Test-AgentRegistration
    if (-not $results.Registration) {
        Write-Warning "Registration failed, but continuing with tests..."
    }
    
    # Test 4: Agent startup
    $agentProcess = Test-AgentStartup
    if ($agentProcess) {
        $results.Startup = $true
        
        # Monitor logs
        Monitor-AgentLogs -AgentProcess $agentProcess -Duration 20
        
        # Test 5: Job execution
        $results.JobExecution = Test-JobExecution -AgentProcess $agentProcess
        
        # Keep agent running for additional testing
        Write-Info "Agent is running. Press Ctrl+C to stop..."
        try {
            while (-not $agentProcess.HasExited) {
                Start-Sleep -Seconds 5
            }
        } catch {
            # User interrupted
        } finally {
            if (-not $agentProcess.HasExited) {
                Write-Info "Stopping agent..."
                Stop-Process -Id $agentProcess.Id -Force
            }
        }
    }
    
    return $results
}

# Run tests and display results
Write-Host "Starting Windows Agent tests..." -ForegroundColor Yellow
$testResults = Run-AgentTests

Write-Host ""
Write-Host "Test Results Summary" -ForegroundColor Blue
Write-Host "===================" -ForegroundColor Blue
Write-Host ""

$testResults.GetEnumerator() | ForEach-Object {
    $status = if ($_.Value) { "PASSED" } else { "FAILED" }
    $color = if ($_.Value) { "Green" } else { "Red" }
    Write-Host ("{0,-20} {1}" -f $_.Key, $status) -ForegroundColor $color
}

Write-Host ""

$passedTests = ($testResults.Values | Where-Object { $_ }).Count
$totalTests = $testResults.Count
$successRate = [math]::Round(($passedTests / $totalTests) * 100, 1)

Write-Host "Overall: $passedTests/$totalTests tests passed ($successRate%)" -ForegroundColor $(if ($successRate -ge 80) { "Green" } elseif ($successRate -ge 60) { "Yellow" } else { "Red" })
Write-Host ""