# Windows Agent Deployment Script
# This PowerShell script automates the deployment of the Skipper agent on Windows

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$TenantId,
    
    [string]$InstallPath = "$env:ProgramFiles\Skipper\Agent",
    
    [switch]$InstallService,
    
    [switch]$StartAgent,
    
    [switch]$Silent
)

# Set up logging
$LogFile = "$InstallPath\deployment.log"
function Write-Log {
    param($Message, $Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "$Timestamp [$Level] $Message"
    
    if (-not $Silent) {
        switch ($Level) {
            "ERROR" { Write-Host $LogMessage -ForegroundColor Red }
            "WARNING" { Write-Host $LogMessage -ForegroundColor Yellow }
            "SUCCESS" { Write-Host $LogMessage -ForegroundColor Green }
            default { Write-Host $LogMessage }
        }
    }
    
    Add-Content -Path $LogFile -Value $LogMessage -Force
}

# Check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Install Python if not present
function Install-Python {
    Write-Log "Checking Python installation..."
    
    try {
        $pythonVersion = python --version 2>&1
        Write-Log "Python is already installed: $pythonVersion" "SUCCESS"
        return $true
    } catch {
        Write-Log "Python not found. Installing Python..." "WARNING"
        
        # Download Python installer
        $pythonUrl = "https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe"
        $installerPath = "$env:TEMP\python-installer.exe"
        
        Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath
        
        # Install Python silently
        Start-Process -FilePath $installerPath -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1" -Wait
        
        # Refresh environment
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-Log "Python installed successfully" "SUCCESS"
        return $true
    }
}

# Create directory structure
function Initialize-Directories {
    Write-Log "Creating directory structure..."
    
    $directories = @(
        $InstallPath,
        "$InstallPath\agent",
        "$InstallPath\config",
        "$InstallPath\logs",
        "$InstallPath\packages",
        "$InstallPath\work"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Log "Created directory: $dir"
        }
    }
}

# Download agent files
function Download-AgentFiles {
    Write-Log "Downloading agent files..."
    
    # In production, this would download from a release server
    # For now, we'll assume files are in current directory
    
    $agentFiles = @(
        "agent\__init__.py",
        "agent\agent_main.py",
        "agent\agent_config.py",
        "agent\api_client.py",
        "agent\auto_login_manager.py",
        "agent\execution_context.py",
        "agent\job_executor.py",
        "agent\package_manager.py",
        "run_agent.py",
        "windows_agent_fix.py",
        "requirements.txt"
    )
    
    foreach ($file in $agentFiles) {
        $sourcePath = Join-Path $PSScriptRoot $file
        $destPath = Join-Path $InstallPath $file
        
        if (Test-Path $sourcePath) {
            $destDir = Split-Path $destPath -Parent
            if (-not (Test-Path $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }
            
            Copy-Item -Path $sourcePath -Destination $destPath -Force
            Write-Log "Copied: $file"
        } else {
            Write-Log "File not found: $file" "WARNING"
        }
    }
}

# Install Python dependencies
function Install-Dependencies {
    Write-Log "Installing Python dependencies..."
    
    $requirementsPath = Join-Path $InstallPath "requirements.txt"
    
    if (Test-Path $requirementsPath) {
        try {
            & python -m pip install --upgrade pip
            & python -m pip install -r $requirementsPath
            
            # Install Windows-specific packages
            & python -m pip install pywin32 pystray pillow
            
            Write-Log "Dependencies installed successfully" "SUCCESS"
        } catch {
            Write-Log "Error installing dependencies: $_" "ERROR"
            return $false
        }
    } else {
        Write-Log "requirements.txt not found" "WARNING"
    }
    
    return $true
}

# Create agent configuration
function Create-Configuration {
    Write-Log "Creating agent configuration..."
    
    $configPath = Join-Path $InstallPath "config\agent_config.json"
    
    # Get machine information
    $machineId = (Get-WmiObject Win32_ComputerSystemProduct).UUID
    $hostname = $env:COMPUTERNAME
    
    $config = @{
        server_url = $ServerUrl
        tenant_id = $TenantId
        machine_id = $machineId
        name = "Windows-$hostname"
        version = "1.0.0"
        capabilities = @{
            packages = @("python", "pyautogui", "pywin32")
            system = @{
                platform = "windows"
                display_available = $true
                automation_ui = $true
                office_automation = $true
            }
        }
        settings = @{
            log_level = "INFO"
            heartbeat_interval = 30
            job_poll_interval = 15
            headless = $false
            packages_dir = "$InstallPath\packages"
            working_dir = "$InstallPath\work"
            verify_ssl = $true
        }
    }
    
    $config | ConvertTo-Json -Depth 10 | Set-Content -Path $configPath
    Write-Log "Configuration created at: $configPath" "SUCCESS"
}

# Register agent with server
function Register-Agent {
    Write-Log "Registering agent with server..."
    
    $scriptPath = Join-Path $InstallPath "windows_agent_fix.py"
    
    try {
        & python $scriptPath $ServerUrl $TenantId
        Write-Log "Agent registered successfully" "SUCCESS"
        return $true
    } catch {
        Write-Log "Failed to register agent: $_" "ERROR"
        return $false
    }
}

# Create Windows service
function Install-WindowsService {
    if (-not (Test-Administrator)) {
        Write-Log "Administrator privileges required for service installation" "ERROR"
        return $false
    }
    
    Write-Log "Creating Windows service..."
    
    # Create service wrapper script
    $serviceScript = @'
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

class SkipperAgentService(win32serviceutil.ServiceFramework):
    _svc_name_ = "SkipperAgent"
    _svc_display_name_ = "Skipper Automation Agent"
    _svc_description_ = "Executes automation tasks from Skipper orchestrator"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        
    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                            servicemanager.PYS_SERVICE_STARTED,
                            (self._svc_name_, ''))
        self.main()
        
    def main(self):
        os.chdir(r'{}')
        sys.path.insert(0, r'{}')
        
        # Import and run the agent
        import run_agent
        run_agent.main()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SkipperAgentService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(SkipperAgentService)
'@ -f $InstallPath, $InstallPath
    
    $servicePath = Join-Path $InstallPath "agent_service.py"
    $serviceScript | Set-Content -Path $servicePath
    
    try {
        # Install the service
        & python $servicePath install
        
        # Configure service to start automatically
        Set-Service -Name "SkipperAgent" -StartupType Automatic
        
        Write-Log "Windows service installed successfully" "SUCCESS"
        return $true
    } catch {
        Write-Log "Failed to install service: $_" "ERROR"
        return $false
    }
}

# Create start menu shortcuts
function Create-Shortcuts {
    Write-Log "Creating shortcuts..."
    
    $startMenuPath = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Skipper Agent"
    
    if (-not (Test-Path $startMenuPath)) {
        New-Item -ItemType Directory -Path $startMenuPath -Force | Out-Null
    }
    
    # Create Start Agent shortcut
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut("$startMenuPath\Start Agent.lnk")
    $shortcut.TargetPath = "python.exe"
    $shortcut.Arguments = "`"$InstallPath\run_agent.py`""
    $shortcut.WorkingDirectory = $InstallPath
    $shortcut.IconLocation = "python.exe"
    $shortcut.Description = "Start Skipper Agent"
    $shortcut.Save()
    
    # Create Agent Logs shortcut
    $shortcut = $shell.CreateShortcut("$startMenuPath\Agent Logs.lnk")
    $shortcut.TargetPath = "notepad.exe"
    $shortcut.Arguments = "`"$InstallPath\agent.log`""
    $shortcut.IconLocation = "notepad.exe"
    $shortcut.Description = "View Agent Logs"
    $shortcut.Save()
    
    Write-Log "Shortcuts created" "SUCCESS"
}

# Main deployment function
function Deploy-Agent {
    Write-Log "Starting Skipper Agent deployment..."
    Write-Log "Server URL: $ServerUrl"
    Write-Log "Tenant ID: $TenantId"
    Write-Log "Install Path: $InstallPath"
    
    # Check prerequisites
    if ($InstallService -and -not (Test-Administrator)) {
        Write-Log "Please run this script as Administrator to install the Windows service" "ERROR"
        return $false
    }
    
    # Create directories
    Initialize-Directories
    
    # Install Python if needed
    if (-not (Install-Python)) {
        return $false
    }
    
    # Download agent files
    Download-AgentFiles
    
    # Install dependencies
    if (-not (Install-Dependencies)) {
        return $false
    }
    
    # Create configuration
    Create-Configuration
    
    # Register agent
    if (-not (Register-Agent)) {
        return $false
    }
    
    # Install Windows service if requested
    if ($InstallService) {
        if (-not (Install-WindowsService)) {
            Write-Log "Service installation failed, but agent is ready to run manually" "WARNING"
        }
    }
    
    # Create shortcuts
    Create-Shortcuts
    
    # Start agent if requested
    if ($StartAgent) {
        if ($InstallService) {
            Write-Log "Starting agent service..."
            Start-Service -Name "SkipperAgent"
        } else {
            Write-Log "Starting agent..."
            Start-Process -FilePath "python.exe" -ArgumentList "$InstallPath\run_agent.py" -WorkingDirectory $InstallPath
        }
    }
    
    Write-Log "Deployment completed successfully!" "SUCCESS"
    Write-Log "Agent is installed at: $InstallPath"
    
    if (-not $StartAgent) {
        Write-Log "To start the agent:"
        Write-Log "  Manual: python `"$InstallPath\run_agent.py`""
        if ($InstallService) {
            Write-Log "  Service: Start-Service SkipperAgent"
        }
    }
    
    return $true
}

# Execute deployment
try {
    if (Deploy-Agent) {
        exit 0
    } else {
        exit 1
    }
} catch {
    Write-Log "Deployment failed: $_" "ERROR"
    exit 1
}