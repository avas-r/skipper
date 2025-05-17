# Windows Agent Communication Test Script (PowerShell)
# This script provides comprehensive testing for Windows agent communication

$ServerUrl = "http://localhost:8000"
$TenantId = "test-tenant"
$MockServerPort = 8000

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

# Check if Python is installed
function Test-PythonInstalled {
    try {
        $pythonVersion = python --version 2>&1
        Write-Success "✓ Python installed: $pythonVersion"
        return $true
    } catch {
        Write-Error "✗ Python is not installed or not in PATH"
        return $false
    }
}

# Start mock server
function Start-MockServer {
    Write-Info "Starting mock server on port $MockServerPort..."
    $mockServerProcess = Start-Process python -ArgumentList "simple_mock_server.py" -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 3
    
    # Test if server is running
    try {
        $response = Invoke-RestMethod -Uri "$ServerUrl/" -Method Get
        Write-Success "✓ Mock server is running"
        return $mockServerProcess
    } catch {
        Write-Error "✗ Failed to start mock server"
        return $null
    }
}

# Register agent
function Register-Agent {
    param($ServerUrl, $TenantId)
    
    Write-Info "Registering Windows agent..."
    $output = python windows_agent_fix.py $ServerUrl $TenantId 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Agent registered successfully"
        return $true
    } else {
        Write-Error "✗ Failed to register agent"
        Write-Error $output
        return $false
    }
}

# Run agent
function Start-Agent {
    param($ServerUrl, $TenantId, $Headless = $false)
    
    $args = @("run_agent.py", "--server", $ServerUrl, "--tenant", $TenantId)
    if ($Headless) {
        $args += "--headless"
    }
    
    Write-Info "Starting agent..."
    $agentProcess = Start-Process python -ArgumentList $args -PassThru -WindowStyle Hidden
    return $agentProcess
}

# Monitor agent logs
function Monitor-AgentLogs {
    if (Test-Path "agent.log") {
        Write-Info "Monitoring agent logs..."
        Get-Content "agent.log" -Wait -Tail 10
    } else {
        Write-Warning "No agent.log file found"
    }
}

# Check agent status via API
function Get-AgentStatus {
    try {
        $agents = Invoke-RestMethod -Uri "$ServerUrl/api/v1/agents" -Method Get
        
        if ($agents.Count -gt 0) {
            Write-Success "✓ Found $($agents.Count) registered agents:"
            foreach ($agent in $agents) {
                Write-Info "  - $($agent.name) (Status: $($agent.status))"
            }
        } else {
            Write-Warning "No agents found"
        }
    } catch {
        Write-Error "✗ Failed to retrieve agent status"
    }
}

# Main menu
function Show-Menu {
    Write-Host ""
    Write-Host "Windows Agent Communication Test" -ForegroundColor Blue
    Write-Host "================================" -ForegroundColor Blue
    Write-Host ""
    Write-Host "1. Check prerequisites"
    Write-Host "2. Start mock server"
    Write-Host "3. Register Windows agent"
    Write-Host "4. Run agent (normal mode)"
    Write-Host "5. Run agent (headless mode)"
    Write-Host "6. Check agent status"
    Write-Host "7. Monitor agent logs"
    Write-Host "8. Run full test cycle"
    Write-Host "9. Clean up and exit"
    Write-Host ""
    
    $choice = Read-Host "Select option (1-9)"
    return $choice
}

# Full test cycle
function Run-FullTest {
    Write-Info "Running full communication test..."
    Write-Host ""
    
    # Check Python
    if (-not (Test-PythonInstalled)) {
        return
    }
    
    # Start mock server
    $mockServer = Start-MockServer
    if (-not $mockServer) {
        return
    }
    
    # Register agent
    if (-not (Register-Agent -ServerUrl $ServerUrl -TenantId $TenantId)) {
        Stop-Process -Id $mockServer.Id -Force
        return
    }
    
    # Run agent
    $agent = Start-Agent -ServerUrl $ServerUrl -TenantId $TenantId -Headless $true
    Write-Info "Agent running for 30 seconds..."
    
    # Monitor for 30 seconds
    for ($i = 1; $i -le 30; $i++) {
        Write-Progress -Activity "Running agent test" -Status "$i/30 seconds" -PercentComplete (($i/30)*100)
        Start-Sleep -Seconds 1
    }
    
    # Check status
    Get-AgentStatus
    
    # Stop processes
    Write-Info "Stopping processes..."
    Stop-Process -Id $agent.Id -Force
    Stop-Process -Id $mockServer.Id -Force
    
    Write-Success "✓ Test completed"
}

# Main loop
$continue = $true
while ($continue) {
    $choice = Show-Menu
    
    switch ($choice) {
        "1" { Test-PythonInstalled }
        "2" { $mockServer = Start-MockServer }
        "3" { Register-Agent -ServerUrl $ServerUrl -TenantId $TenantId }
        "4" { $agent = Start-Agent -ServerUrl $ServerUrl -TenantId $TenantId }
        "5" { $agent = Start-Agent -ServerUrl $ServerUrl -TenantId $TenantId -Headless $true }
        "6" { Get-AgentStatus }
        "7" { Monitor-AgentLogs }
        "8" { Run-FullTest }
        "9" {
            Write-Info "Cleaning up..."
            Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
            $continue = $false
        }
        default { Write-Warning "Invalid choice" }
    }
    
    if ($continue) {
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
}

Write-Host "Goodbye!" -ForegroundColor Green