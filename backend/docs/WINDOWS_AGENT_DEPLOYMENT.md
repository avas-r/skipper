# Windows Agent Deployment Guide

This guide provides complete instructions for deploying the Skipper automation agent on Windows machines.

## Prerequisites

- Windows 10/11 or Windows Server 2016+
- Python 3.7 or higher
- Administrator privileges (for service installation)
- Network connectivity to the orchestrator server

## Quick Start

1. **Download the agent package**
   ```powershell
   # Clone the repository or download the agent files
   git clone https://github.com/your-org/skipper.git
   cd skipper/backend
   ```

2. **Run the setup script**
   ```powershell
   python windows_agent_setup.py --server https://your-orchestrator.com --tenant your-tenant-id --install-deps
   ```

3. **Register the agent**
   ```powershell
   python windows_agent_fix.py https://your-orchestrator.com your-tenant-id
   ```

4. **Start the agent**
   ```powershell
   python run_agent.py
   ```

## Detailed Installation

### Step 1: System Requirements Check

Verify Python installation:
```powershell
python --version
```

Check system information:
```powershell
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
```

### Step 2: Install Dependencies

Required Python packages:
```powershell
pip install requests psutil cryptography pystray pillow pyautogui schedule
```

Optional packages for enhanced functionality:
```powershell
# For Office automation
pip install pywin32

# For web automation
pip install selenium

# For advanced UI automation
pip install pywinauto
```

### Step 3: Configure the Agent

Run the setup script:
```powershell
python windows_agent_setup.py --server https://your-orchestrator.com --tenant your-tenant-id
```

This will create:
- Configuration file: `~/.orchestrator/agent_config.json`
- Startup batch file: `start_agent.bat`
- Package directory: `~/.orchestrator/packages/`
- Working directory: `~/.orchestrator/work/`

### Step 4: Register with Orchestrator

```powershell
python windows_agent_fix.py https://your-orchestrator.com your-tenant-id
```

This will:
- Generate a unique machine ID
- Register the agent with the server
- Save API credentials

### Step 5: Run the Agent

#### Option 1: Command Line
```powershell
python run_agent.py
```

#### Option 2: Batch File
```powershell
.\start_agent.bat
```

#### Option 3: Windows Service (requires admin)
```powershell
# Install service
python agent_service.py install

# Start service
python agent_service.py start

# Check service status
python agent_service.py status
```

## Configuration Options

### Agent Configuration File

Located at `~/.orchestrator/agent_config.json`:

```json
{
  "server_url": "https://your-orchestrator.com",
  "tenant_id": "your-tenant-id",
  "machine_id": "unique-machine-id",
  "name": "Windows-HOSTNAME",
  "capabilities": {
    "packages": ["python", "pyautogui"],
    "system": {
      "platform": "windows",
      "display_available": true,
      "automation_ui": true,
      "web_automation": false,
      "office_automation": false
    }
  },
  "settings": {
    "log_level": "INFO",
    "heartbeat_interval": 30,
    "job_poll_interval": 15,
    "headless": false,
    "packages_dir": "~/.orchestrator/packages",
    "working_dir": "~/.orchestrator/work"
  }
}
```

### Environment Variables

- `AGENT_HEADLESS`: Set to "1" for headless mode
- `AGENT_LOG_LEVEL`: Override log level (DEBUG, INFO, WARNING, ERROR)
- `AGENT_CONFIG_PATH`: Custom config file location

## Security Configuration

### SSL/TLS

For self-signed certificates:
```json
{
  "settings": {
    "verify_ssl": false
  }
}
```

For custom CA certificates:
```json
{
  "settings": {
    "certificate_path": "C:\\path\\to\\ca-bundle.crt"
  }
}
```

### Service Account

Run agent with limited privileges:
```powershell
# Create service account
net user SkipperAgent PasswordHere /add

# Grant necessary permissions
icacls "C:\Users\SkipperAgent\.orchestrator" /grant SkipperAgent:(OI)(CI)F
```

## Windows-Specific Features

### Auto-Login Configuration

Enable auto-login for unattended automation:
```powershell
python run_agent.py --configure-auto-login
```

### System Tray Icon

The agent shows a system tray icon when running in attended mode:
- Right-click for menu options
- View status
- Manual sync
- Quit agent

### RDP Session Detection

The agent automatically detects RDP sessions and adjusts behavior accordingly.

## Monitoring and Logs

### Log Files

- Agent log: `agent.log` in the current directory
- Execution logs: `~/.orchestrator/work/<execution-id>/logs/`

### View Logs

```powershell
# Real-time log monitoring
Get-Content agent.log -Wait -Tail 20

# Search logs
Select-String -Path agent.log -Pattern "ERROR"
```

### Performance Monitoring

The agent sends system metrics with each heartbeat:
- CPU usage
- Memory usage
- Disk usage
- Active jobs count

## Troubleshooting

### Common Issues

1. **Network Connectivity**
   ```powershell
   # Test server connection
   Test-NetConnection your-orchestrator.com -Port 443
   ```

2. **Firewall Issues**
   ```powershell
   # Allow Python through firewall
   netsh advfirewall firewall add rule name="Python" dir=in action=allow program="C:\Python39\python.exe"
   ```

3. **Permission Errors**
   - Run PowerShell as Administrator
   - Check folder permissions

4. **Service Won't Start**
   ```powershell
   # Check service logs
   eventvwr.msc
   # Navigate to: Windows Logs > Application
   ```

### Debug Mode

Run agent in debug mode:
```powershell
python run_agent.py --debug
```

## Automation Capabilities

### UI Automation

The agent supports:
- Mouse and keyboard control
- Screenshot capture
- Window management
- GUI element interaction

### Web Automation

With Selenium installed:
- Browser automation
- Web scraping
- Form filling
- JavaScript execution

### Office Automation

With pywin32 installed:
- Excel automation
- Word automation
- Outlook automation
- PowerPoint automation

## Deployment Best Practices

1. **Use Service Accounts**
   - Don't run with admin privileges
   - Create dedicated service account

2. **Enable Monitoring**
   - Set up log rotation
   - Monitor system resources
   - Alert on failures

3. **Security Hardening**
   - Use HTTPS only
   - Verify SSL certificates
   - Limit network access

4. **High Availability**
   - Deploy multiple agents
   - Use load balancing
   - Implement failover

5. **Updates and Maintenance**
   - Regular agent updates
   - Automated restarts
   - Health checks

## Example Automation Scripts

### Simple UI Automation

```python
def automate_notepad(context):
    import pyautogui
    import time
    
    # Open Notepad
    pyautogui.press('win')
    time.sleep(1)
    pyautogui.write('notepad')
    pyautogui.press('enter')
    time.sleep(2)
    
    # Type some text
    pyautogui.write('Hello from automation!')
    
    # Take screenshot
    screenshot = pyautogui.screenshot()
    screenshot.save('notepad_automation.png')
    
    # Close Notepad
    pyautogui.hotkey('alt', 'f4')
    time.sleep(1)
    pyautogui.press('n')  # Don't save
    
    context.log("Notepad automation completed")
    return {"status": "success", "screenshot": "notepad_automation.png"}
```

### Web Automation Example

```python
def automate_web(context):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    
    # Get credentials from context
    username = context.get_asset('web_username')
    password = context.get_asset('web_password')
    
    # Initialize browser
    driver = webdriver.Chrome()
    
    try:
        # Navigate to website
        driver.get('https://example.com/login')
        
        # Login
        driver.find_element(By.ID, 'username').send_keys(username)
        driver.find_element(By.ID, 'password').send_keys(password)
        driver.find_element(By.ID, 'login-button').click()
        
        # Perform tasks...
        
        context.log("Web automation completed")
        return {"status": "success"}
    finally:
        driver.quit()
```

## Support and Resources

- Documentation: https://docs.skipper.io
- GitHub: https://github.com/your-org/skipper
- Support: support@skipper.io

For enterprise support, contact your system administrator.