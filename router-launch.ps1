param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$ProfileName,

    [string]$RouterUrl = "http://127.0.0.1:3459",
    [string]$ProjectRoot = $PSScriptRoot
)

# Load the agent profile to find which harness it uses.
$slug = $ProfileName.ToLower() -replace ' ', '-'
$agentPath = Join-Path $ProjectRoot "profiles\agents\$slug.json"

if (-not (Test-Path $agentPath)) {
    Write-Host "No agent profile found for '$ProfileName' (looked for $agentPath)" -ForegroundColor Red
    exit 1
}

$agent = Get-Content $agentPath -Raw | ConvertFrom-Json
$harnessName = $agent.harness

# Load the harness profile
$harnessPath = Join-Path $ProjectRoot "profiles\harnesses\$harnessName.json"
if (-not (Test-Path $harnessPath)) {
    Write-Host "No harness profile found: $harnessPath" -ForegroundColor Red
    exit 1
}
$harness = Get-Content $harnessPath -Raw | ConvertFrom-Json

Write-Host "Launching [$harnessName] with agent profile: $ProfileName" -ForegroundColor Cyan
Write-Host "Router: $RouterUrl" -ForegroundColor DarkGray
Write-Host "Model: $($agent.model)" -ForegroundColor DarkGray
Write-Host ""

switch ($harness.launch_mode) {

    # ─── Claude Code: env vars only ───────────────────────────────────
    "env" {
        $env:ANTHROPIC_BASE_URL = $RouterUrl
        $env:ANTHROPIC_AUTH_TOKEN = $ProfileName
        & $harness.binary
    }

    # ─── OpenCode: project-local config file ──────────────────────────
    "config_file" {
        $configPath = Join-Path $ProjectRoot $harness.config_file_path

        # Build config from template, replacing placeholders
        $configJson = $harness.config_template | ConvertTo-Json -Depth 10
        $configJson = $configJson -replace '\{\{base_url\}\}', "$RouterUrl/v1"
        $configJson = $configJson -replace '\{\{model\}\}', $agent.model
        $configJson | Out-File -Encoding utf8 -FilePath $configPath

        Write-Host "Config written: $configPath" -ForegroundColor DarkGray

        # OpenCode also needs an API key env var (can be anything since router handles auth)
        $env:OPENAI_API_KEY = $ProfileName

        $args = @()
        if ($harness.extra_args) { $args = $harness.extra_args }

        Push-Location $ProjectRoot
        & $harness.binary @args
        Pop-Location
    }

    # ─── DeepSeek Harness: config file + env var ──────────────────────
    "config_file_plus_env" {
        # Set the auth env var (router uses it as profile identifier)
        $envMap = $harness.env_map
        if ($envMap.auth_token) {
            [Environment]::SetEnvironmentVariable($envMap.auth_token, $ProfileName, "Process")
        }

        # Build YAML config from template
        $configPath = $harness.config_file_path -replace '~', $env:USERPROFILE
        $configDir = Split-Path $configPath -Parent
        if (-not (Test-Path $configDir)) {
            New-Item -ItemType Directory -Path $configDir -Force | Out-Null
        }

        # Simple YAML generation from template
        $yaml = @"
provider:
  custom:
    base_url: $RouterUrl/v1
    protocol: openai-compatible
    models:
      - $($agent.model)
"@
        $yaml | Out-File -Encoding utf8 -FilePath $configPath

        Write-Host "Config written: $configPath" -ForegroundColor DarkGray

        $args = @()
        if ($harness.extra_args) { $args = $harness.extra_args }

        & $harness.binary @args
    }

    default {
        Write-Host "Unknown launch_mode '$($harness.launch_mode)' in harness '$harnessName'" -ForegroundColor Red
        exit 1
    }
}
