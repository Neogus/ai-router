#!/usr/bin/env pwsh
# ai-router.ps1 - CLI tool for AI Router service and agent management
# Usage: ai-router <command> [args]

param(
    [Parameter(Position=0)]
    [string]$Command,

    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$RestArgs
)

$ErrorActionPreference = "Stop"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = $SCRIPT_DIR
$SERVICE_NAME = "AIRouter"
$PORT = 3459

function Get-NssmPath {
    $n = (Get-Command nssm -ErrorAction SilentlyContinue).Source
    if ($n) { return $n }
    $arch = if ([Environment]::Is64BitOperatingSystem) { "win64" } else { "win32" }
    $local = Join-Path $PROJECT_ROOT "tools\nssm-2.24\$arch\nssm.exe"
    if (Test-Path $local) { return $local }
    return $null
}

function Get-ServiceStatus {
    $svc = Get-Service -Name $SERVICE_NAME -ErrorAction SilentlyContinue
    if (-not $svc) { return "NOT_INSTALLED" }
    return $svc.Status.ToString()
}

function Show-Help {
    Write-Host ""
    Write-Host "  AI Router CLI" -ForegroundColor Cyan
    Write-Host "  Usage: ai-router <command> [args]" -ForegroundColor White
    Write-Host ""
    Write-Host "  Commands:" -ForegroundColor Yellow
    Write-Host "    launch <profile>   Launch an agent in new terminal"
    Write-Host "    ui                 Open dashboard in browser"
    Write-Host "    start              Start the service"
    Write-Host "    stop               Stop the service"
    Write-Host "    restart            Restart the service"
    Write-Host "    status             Show service status"
    Write-Host "    list               List available agent profiles"
    Write-Host "    install            Run the service installer (admin)"
    Write-Host "    help               Show this help"
    Write-Host ""
    Write-Host "  Examples:" -ForegroundColor Gray
    Write-Host "    ai-router launch aider-open-nemotron-free"
    Write-Host "    ai-router launch 'Gemini'"
    Write-Host "    ai-router ui"
    Write-Host ""
}

function Invoke-ServiceCmd {
    param([string]$Action)
    $nssm = Get-NssmPath
    if (-not $nssm) { Write-Host "ERROR: NSSM not found. Run: ai-router install" -ForegroundColor Red; exit 1 }

    switch ($Action) {
        "start" {
            Write-Host "Starting $SERVICE_NAME..." -ForegroundColor Cyan
            & $nssm start $SERVICE_NAME 2>&1 | Out-Null
            Start-Sleep -Seconds 2
            $s = Get-ServiceStatus
            if ($s -eq "Running") { Write-Host "OK - running on http://127.0.0.1:$PORT" -ForegroundColor Green }
            else { Write-Host "Status: $s" -ForegroundColor Yellow }
        }
        "stop" {
            Write-Host "Stopping $SERVICE_NAME..." -ForegroundColor Cyan
            & $nssm stop $SERVICE_NAME 2>&1 | Out-Null
            Write-Host "Stopped." -ForegroundColor Green
        }
        "restart" {
            Write-Host "Restarting $SERVICE_NAME..." -ForegroundColor Cyan
            & $nssm restart $SERVICE_NAME 2>&1 | Out-Null
            Start-Sleep -Seconds 3
            $s = Get-ServiceStatus
            if ($s -eq "Running") { Write-Host "OK - running on http://127.0.0.1:$PORT" -ForegroundColor Green }
            else { Write-Host "Status: $s" -ForegroundColor Yellow }
        }
    }
}

function Show-Status {
    $status = Get-ServiceStatus
    Write-Host ""
    Write-Host "  AI Router" -ForegroundColor Cyan
    if ($status -eq "NOT_INSTALLED") {
        Write-Host "  Status: NOT INSTALLED" -ForegroundColor Red
        Write-Host "  Run: ai-router install" -ForegroundColor Yellow
    } else {
        $c = if ($status -eq "Running") { "Green" } else { "Yellow" }
        Write-Host "  Service: $SERVICE_NAME" -ForegroundColor White
        Write-Host "  Status:  $status" -ForegroundColor $c
        Write-Host "  Port:    $PORT" -ForegroundColor White
        if ($status -eq "Running") {
            try {
                $r = Invoke-RestMethod -Uri "http://127.0.0.1:$PORT/api/status" -TimeoutSec 2 -ErrorAction Stop
                Write-Host "  Agents:  $($r.agents)" -ForegroundColor Gray
                Write-Host "  URL:     http://127.0.0.1:$PORT/ui" -ForegroundColor Gray
            } catch {
                Write-Host "  Health:  Could not connect" -ForegroundColor Yellow
            }
        }
    }
    Write-Host ""
}

function Show-AgentList {
    $agentsDir = Join-Path $PROJECT_ROOT "profiles\agents"
    $files = Get-ChildItem -Path $agentsDir -Filter "*.json" | Sort-Object Name

    Write-Host ""
    Write-Host "  Agent Profiles ($($files.Count))" -ForegroundColor Cyan
    Write-Host ""

    foreach ($f in $files) {
        try {
            $j = Get-Content $f.FullName -Raw | ConvertFrom-Json
            $native = if ($j.native) { " [native]" } else { "" }
            $model = if ($j.model) { $j.model } else { "(default)" }
            Write-Host "  $($f.BaseName)" -ForegroundColor White -NoNewline
            Write-Host "$native" -ForegroundColor Magenta
            Write-Host "    $($j.harness) | $($j.provider) | $model" -ForegroundColor Gray
        } catch {}
    }
    Write-Host ""
}

function Invoke-LaunchAgent {
    param([string]$ProfileName)
    if (-not $ProfileName) {
        Write-Host "ERROR: Profile name required" -ForegroundColor Red
        Write-Host "Usage: ai-router launch <profile-name-or-slug>" -ForegroundColor Yellow
        exit 1
    }

    # Ensure service is running
    $s = Get-ServiceStatus
    if ($s -ne "Running") {
        Write-Host "Service not running. Starting..." -ForegroundColor Yellow
        Invoke-ServiceCmd "start"
    }

    # Slugify: lowercase, replace spaces with dashes, URL-encode special chars
    $slug = $ProfileName.ToLower().Trim() -replace '\s+', '-'
    $slug = [Uri]::EscapeDataString($slug)

    # Get launch config from API (GET = config only, no new window)
    try {
        $url = "http://127.0.0.1:$PORT/api/launch/$slug"
        $config = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 5 -ErrorAction Stop
    } catch {
        $err = "Could not connect or agent not found"
        try {
            if ($_.Exception.Response) {
                $stream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($stream)
                $respBody = $reader.ReadToEnd()
                $parsed = $respBody | ConvertFrom-Json
                if ($parsed.error) { $err = $parsed.error }
            }
        } catch {}
        Write-Host "ERROR: $err" -ForegroundColor Red
        Write-Host "  Try: ai-router list" -ForegroundColor Gray
        exit 1
    }

    # Set environment variables for this process
    $envVars = $config.env
    if ($envVars) {
        $envVars.PSObject.Properties | ForEach-Object {
            [Environment]::SetEnvironmentVariable($_.Name, $_.Value, "Process")
            Write-Host "  $($_.Name) = $($_.Value)" -ForegroundColor Green
        }
    }

    # Resolve binary and args (prefer .cmd on Windows for npm packages)
    $binary = $config.harness.binary_path
    if (-not $binary) { $binary = $config.harness.binary }
    if ($binary -and -not ($binary -match '\.(exe|cmd|ps1|bat)$')) {
        if (Test-Path "$binary.cmd") { $binary = "$binary.cmd" }
        elseif (Test-Path "$binary.exe") { $binary = "$binary.exe" }
    }

    $extraArgs = @()
    if ($config.harness.extra_args) {
        $model = $config.agent.model
        $baseUrl = if ($envVars -and $envVars.PSObject.Properties.Count -gt 0) {
            ($envVars.PSObject.Properties | Where-Object { $_.Name -match "BASE|URL|HOST" } | Select-Object -First 1).Value
        } else { "" }
        foreach ($a in $config.harness.extra_args) {
            $a = $a -replace '\{\{model\}\}', $model
            $a = $a -replace '\{\{base_url\}\}', $baseUrl
            $a = $a -replace '\{\{auth_token\}\}', $slug
            $extraArgs += $a
        }
    }

    Write-Host "" 
    $agentName = $config.agent.name
    $native = if (-not $envVars -or $envVars.PSObject.Properties.Count -eq 0) { " (native)" } else { "" }
    Write-Host "  Launching: $agentName$native" -ForegroundColor Cyan
    if ($config.agent.model) {
        Write-Host "  Model: $($config.agent.model)" -ForegroundColor Gray
    }
    Write-Host ""

    # Execute inline (replaces this process)
    & $binary @extraArgs
}

function Open-Dashboard {
    $s = Get-ServiceStatus
    if ($s -ne "Running") {
        Write-Host "Service not running. Starting..." -ForegroundColor Yellow
        Invoke-ServiceCmd "start"
        Start-Sleep -Seconds 2
    }
    $url = "http://127.0.0.1:$PORT/ui"
    Write-Host "Opening: $url" -ForegroundColor Cyan
    Start-Process $url
}

function Run-Installer {
    $script = Join-Path $PROJECT_ROOT "install-service.ps1"
    if (-not (Test-Path $script)) {
        Write-Host "ERROR: install-service.ps1 not found" -ForegroundColor Red; exit 1
    }
    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Host "Launching elevated installer..." -ForegroundColor Yellow
        Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
    } else {
        & $script
    }
}

# ── Main dispatcher ──
if (-not $Command) { Show-Help; exit 0 }
$Command = $Command.ToLower()
$ProfileArg = if ($RestArgs) { $RestArgs -join " " } else { "" }

switch ($Command) {
    "help"    { Show-Help }
    "start"   { Invoke-ServiceCmd "start" }
    "stop"    { Invoke-ServiceCmd "stop" }
    "restart" { Invoke-ServiceCmd "restart" }
    "status"  { Show-Status }
    "list"    { Show-AgentList }
    "ui"      { Open-Dashboard }
    "launch"  { Invoke-LaunchAgent $ProfileArg }
    "install" { Run-Installer }
    default   {
        # Treat unknown command as a profile name for launch
        $fullName = "$Command $ProfileArg".Trim()
        Invoke-LaunchAgent $fullName
    }
}
