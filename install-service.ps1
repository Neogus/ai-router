# install-service.ps1 - Install AI Router as an NSSM Windows service
# Run as Administrator!

param(
    [string]$ServiceName = "AIRouter",
    [string]$ProjectRoot = $PSScriptRoot,
    [int]$Port = 3459
)

$ErrorActionPreference = "Stop"
trap { Write-Host "`n  ERROR: $_" -ForegroundColor Red; Read-Host "`n  Press Enter to close"; exit 1 }

Write-Host ""
Write-Host "  AI Router Service Installer" -ForegroundColor Cyan
Write-Host ""

# -- Check Admin --
function Test-Administrator {
    $p = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Host "  ERROR: Requires Administrator privileges!" -ForegroundColor Red
    Write-Host "  Right-click PowerShell -> Run as Administrator" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "  Press Enter to close"
    exit 1
}

# -- Find Python --
Write-Host "  [1/5] Detecting Python..." -ForegroundColor Cyan
$python = $null
foreach ($cmd in @("python", "python3")) {
    $p = (Get-Command $cmd -ErrorAction SilentlyContinue).Source
    if ($p) {
        $v = & $p --version 2>&1
        if ($v -match "Python \d+\.\d+") {
            $python = $p
            Write-Host "        Found: $python ($v)" -ForegroundColor Green
            break
        }
    }
}
if (-not $python) {
    Write-Host "  ERROR: Python not found. Install from https://python.org" -ForegroundColor Red
    exit 1
}

# -- Install Requirements --
Write-Host "  [2/5] Installing requirements..." -ForegroundColor Cyan
$reqFile = Join-Path $ProjectRoot "requirements.txt"
try {
    $ErrorActionPreference = "Continue"
    if (Test-Path $reqFile) {
        & $python -m pip install -r $reqFile -q 2>&1 | Out-Null
    } else {
        & $python -m pip install flask requests -q 2>&1 | Out-Null
    }
    $ErrorActionPreference = "Stop"
    Write-Host "        Done (flask, requests)" -ForegroundColor Green
} catch {
    $ErrorActionPreference = "Stop"
    Write-Host "        Warning: pip had issues but continuing..." -ForegroundColor Yellow
}

# -- Setup .env file --
$envFile = Join-Path $ProjectRoot ".env"
$envExample = Join-Path $ProjectRoot ".env.example"
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Host "        Created .env from .env.example (add your API keys!)" -ForegroundColor Yellow
    } else {
        Write-Host "        Warning: No .env file found. Create one with your API keys." -ForegroundColor Yellow
    }
} else {
    Write-Host "        .env already exists" -ForegroundColor Green
}

# -- Setup Gemini CLI settings (required for Gemini harness) --
$geminiSettings = Join-Path $env:USERPROFILE ".gemini\settings.json"
if (-not (Test-Path $geminiSettings)) {
    $geminiDir = Split-Path $geminiSettings -Parent
    New-Item -ItemType Directory -Path $geminiDir -Force | Out-Null
    '{"security":{"auth":{"selectedType":"gemini-api-key"}}}' | Out-File -FilePath $geminiSettings -Encoding utf8
    Write-Host "        Created ~/.gemini/settings.json (for Gemini CLI auth)" -ForegroundColor Green
} else {
    Write-Host "        ~/.gemini/settings.json already exists" -ForegroundColor Green
}

# -- Install/Locate NSSM --
Write-Host "  [3/5] Checking NSSM..." -ForegroundColor Cyan
$nssm = (Get-Command nssm -ErrorAction SilentlyContinue).Source

if (-not $nssm) {
    $toolsDir = Join-Path $ProjectRoot "tools"
    $nssmDir = Join-Path $toolsDir "nssm-2.24"
    $nssmZip = Join-Path $toolsDir "nssm-2.24.zip"
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"

    New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null

    if (-not (Test-Path $nssmDir)) {
        Write-Host "        Downloading NSSM..." -ForegroundColor Gray
        try {
            Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip -UseBasicParsing
            Expand-Archive -Path $nssmZip -DestinationPath $toolsDir -Force
            Remove-Item $nssmZip -Force
        } catch {
            Write-Host "  ERROR: Failed to download NSSM: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "  Manual: download from https://nssm.cc/download or 'winget install nssm'" -ForegroundColor Yellow
            exit 1
        }
    }

    $arch = if ([Environment]::Is64BitOperatingSystem) { "win64" } else { "win32" }
    $nssm = Join-Path $nssmDir "$arch\nssm.exe"

    if (-not (Test-Path $nssm)) {
        Write-Host "  ERROR: NSSM not found at $nssm" -ForegroundColor Red
        exit 1
    }
}
Write-Host "        Using: $nssm" -ForegroundColor Green

# -- Verify router.py --
$routerScript = Join-Path $ProjectRoot "router.py"
if (-not (Test-Path $routerScript)) {
    Write-Host "  ERROR: router.py not found at $routerScript" -ForegroundColor Red
    exit 1
}

# -- Remove existing service --
Write-Host "  [4/5] Configuring service..." -ForegroundColor Cyan
$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "        Removing existing service..." -ForegroundColor Gray
    & $nssm stop $ServiceName 2>&1 | Out-Null
    Start-Sleep -Seconds 2
    & $nssm remove $ServiceName confirm 2>&1 | Out-Null
}

# -- Install service --
$appArgs = "`"$routerScript`" --port $Port"
& $nssm install $ServiceName $python $appArgs
& $nssm set $ServiceName AppDirectory $ProjectRoot
& $nssm set $ServiceName DisplayName "AI Router"
& $nssm set $ServiceName Description "AI Router - Routes coding harnesses to LLM providers"
& $nssm set $ServiceName Start SERVICE_AUTO_START

# Logging
$logsDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
& $nssm set $ServiceName AppStdout (Join-Path $logsDir "stdout.log")
& $nssm set $ServiceName AppStderr (Join-Path $logsDir "stderr.log")
& $nssm set $ServiceName AppRotateFiles 1
& $nssm set $ServiceName AppRotateBytes 1048576
& $nssm set $ServiceName AppRotateOnline 1

Write-Host "        Service configured" -ForegroundColor Green

# Set service to run as current user (for access to user-installed tools)
Write-Host "" 
Write-Host "  The service needs your Windows credentials to access" -ForegroundColor Yellow
Write-Host "  user-installed tools (Python, Node, npm packages)." -ForegroundColor Yellow
Write-Host ""
$cred = Get-Credential -UserName ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -Message "Enter your Windows password for the AI Router service"
if ($cred) {
    $username = $cred.UserName
    $password = $cred.GetNetworkCredential().Password
    & $nssm set $ServiceName ObjectName $username $password 2>&1 | Out-Null
    Write-Host "        Running as: $username" -ForegroundColor Green
} else {
    Write-Host "        Skipped - running as Local System (may not find user tools)" -ForegroundColor Yellow
}

# -- Start --
Write-Host "  [5/5] Starting service..." -ForegroundColor Cyan
& $nssm start $ServiceName 2>&1 | Out-Null
Start-Sleep -Seconds 3

$status = (& $nssm status $ServiceName 2>&1).Trim()
if ($status -match "SERVICE_RUNNING") {
    Write-Host "        Running!" -ForegroundColor Green
} else {
    Write-Host "        Status: $status (check logs\stderr.log)" -ForegroundColor Yellow
}

# -- Add to PATH --
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$ProjectRoot*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$ProjectRoot", "User")
    $env:Path = "$env:Path;$ProjectRoot"
    Write-Host "        Added to PATH (restart terminal for global access)" -ForegroundColor Green
} else {
    Write-Host "        Already in PATH" -ForegroundColor Green
}

# -- Summary --
Write-Host ""
Write-Host "  Installation Complete" -ForegroundColor Green
Write-Host ""
Write-Host "  Dashboard:   http://127.0.0.1:$Port/ui" -ForegroundColor White
Write-Host "  Service:     $ServiceName (auto-start on boot)" -ForegroundColor White
Write-Host "  Logs:        $logsDir" -ForegroundColor White
Write-Host ""
Write-Host "  From any terminal:" -ForegroundColor Yellow
Write-Host "    ai-router status" -ForegroundColor Gray
Write-Host "    ai-router launch aider-open-nemotron-free" -ForegroundColor Gray
Write-Host "    ai-router ui" -ForegroundColor Gray
Write-Host ""
Read-Host "  Press Enter to close"
