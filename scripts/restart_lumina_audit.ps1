[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [ValidateRange(30, 600)]
    [int]$StartupTimeoutSeconds = 240
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$configPath = Join-Path $repoRoot 'config.json'
$profilePath = Join-Path $repoRoot 'logs\runtime_python_execution.json'
$stdoutPath = Join-Path $repoRoot 'logs\lumina_audit_launcher.stdout.log'
$stderrPath = Join-Path $repoRoot 'logs\lumina_audit_launcher.stderr.log'

if (-not (Test-Path -LiteralPath $configPath)) { throw "Missing config: $configPath" }
$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$uiPort = [int]$config.NICEGUI_PORT
$apiPort = [int]$config.BRAIN_API_PORT
$apiHost = if ($config.BRAIN_API_HOST -and $config.BRAIN_API_HOST -notin @('0.0.0.0', '::')) {
    [string]$config.BRAIN_API_HOST
} else { '127.0.0.1' }
$portList = @([int]$config.NICEGUI_PORT, [int]$config.BRAIN_API_PORT)
if ($config.BODY_BRIDGE_LISTEN_ENABLED -and $config.BODY_BRIDGE_LISTEN_PORT) {
    $portList += [int]$config.BODY_BRIDGE_LISTEN_PORT
}
$ports = @($portList | Select-Object -Unique)

function Get-LuminaListeners {
    $listeners = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $ports -contains [int]$_.LocalPort })
    $owners = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
    return [pscustomobject]@{ Listeners = $listeners; OwnerIds = $owners }
}

function Get-WinProcess([int]$ProcessId) {
    Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
}

function Get-VerifiedAuditInstance {
    $network = Get-LuminaListeners
    if ($network.OwnerIds.Count -eq 0) { return $null }
    if ($network.OwnerIds.Count -ne 1) {
        throw "Lumina ports have multiple owners ($($network.OwnerIds -join ', ')); refusing to stop or start anything."
    }

    $serverPid = [int]$network.OwnerIds[0]
    $server = Get-WinProcess $serverPid
    if (-not $server -or $server.CommandLine -notmatch 'scripts[\\/]audit_llm_calls\.py\s+app\.py') {
        throw "PID $serverPid owns a configured Lumina port but is not positively identified as this audit launcher; refusing to stop it."
    }
    if (-not (Test-Path -LiteralPath $profilePath)) {
        throw "Audit profile is missing; refusing to infer that PID $serverPid belongs to this project."
    }
    $profile = Get-Content -LiteralPath $profilePath -Raw | ConvertFrom-Json
    if ([int]$profile.pid -ne $serverPid -or -not $profile.profiling_enabled) {
        throw "Audit profile PID does not match listener PID $serverPid; refusing to stop it."
    }

    $wrapperPid = [int]$server.ParentProcessId
    $wrapper = Get-WinProcess $wrapperPid
    $expectedVenv = (Join-Path $repoRoot 'venv\Scripts\python.exe')
    if (-not $wrapper -or
        $wrapper.ExecutablePath -ine $expectedVenv -or
        $wrapper.CommandLine -notmatch 'scripts[\\/]audit_llm_calls\.py\s+app\.py') {
        throw "PID $serverPid is verified, but its audit wrapper PID $wrapperPid is not this repository's venv launcher; refusing to signal an unverified console group."
    }

    [pscustomobject]@{
        ServerPid = $serverPid
        WrapperPid = $wrapperPid
        Network = $network
        Server = $server
        Wrapper = $wrapper
    }
}

function Test-PortsFree {
    (Get-LuminaListeners).OwnerIds.Count -eq 0
}

function Wait-ForPortsFree([int[]]$ProcessIds, [int]$TimeoutSeconds = 45) {
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        $alive = @($ProcessIds | Where-Object { Get-WinProcess $_ })
        if ($alive.Count -eq 0 -and (Test-PortsFree)) { return }
        Start-Sleep -Milliseconds 300
    } while ([DateTime]::UtcNow -lt $deadline)
    $network = Get-LuminaListeners
    throw "Graceful shutdown did not release the audit process/ports in ${TimeoutSeconds}s. Remaining PIDs: $($network.OwnerIds -join ', '). No force-kill was attempted."
}

function Test-LuminaReady {
    try {
        $status = Invoke-RestMethod -Uri "http://${apiHost}:${apiPort}/status" -TimeoutSec 4
        $next = Invoke-WebRequest -Uri "http://127.0.0.1:${uiPort}/next/" -TimeoutSec 4 -UseBasicParsing
        $network = Get-LuminaListeners
        if ($network.OwnerIds.Count -ne 1) { return $null }
        $serverPid = [int]$network.OwnerIds[0]
        if (-not (Test-Path -LiteralPath $profilePath)) { return $null }
        $profile = Get-Content -LiteralPath $profilePath -Raw | ConvertFrom-Json
        if ([int]$profile.pid -ne $serverPid) { return $null }
        if (-not $status.ready -or $next.StatusCode -ne 200) { return $null }
        return [pscustomobject]@{
            ProcessId = $serverPid
            Status = $status
            NextHttpStatus = $next.StatusCode
            Ports = @($network.Listeners | Select-Object -ExpandProperty LocalPort -Unique)
        }
    } catch { return $null }
}

if ($CheckOnly) {
    $instance = Get-VerifiedAuditInstance
    if (-not $instance) {
        Write-Output 'No Lumina audit instance is listening on the configured ports.'
        exit 0
    }
    $ready = Test-LuminaReady
    if (-not $ready) { throw "Verified audit PID $($instance.ServerPid) owns the ports but is not yet HTTP-ready." }
    $ready | ConvertTo-Json -Depth 4
    exit 0
}

# Inspect first. Unknown processes on any configured port are never stopped.
$instance = Get-VerifiedAuditInstance
if ($instance) {
    Write-Output "Gracefully stopping verified Lumina audit PID $($instance.ServerPid), console wrapper $($instance.WrapperPid)."
    if (-not ('LuminaAuditConsoleControl' -as [type])) {
        Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class LuminaAuditConsoleControl {
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool FreeConsole();
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool AttachConsole(uint processId);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool SetConsoleCtrlHandler(IntPtr handler, bool add);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool GenerateConsoleCtrlEvent(uint ctrlEvent, uint processGroupId);
}
'@
    }
    [LuminaAuditConsoleControl]::FreeConsole() | Out-Null
    if (-not [LuminaAuditConsoleControl]::AttachConsole([uint32]$instance.WrapperPid)) {
        throw "Cannot attach to verified console wrapper $($instance.WrapperPid) (Win32 error $([Runtime.InteropServices.Marshal]::GetLastWin32Error())). No process was stopped."
    }
    [LuminaAuditConsoleControl]::SetConsoleCtrlHandler([IntPtr]::Zero, $true) | Out-Null
    $sent = [LuminaAuditConsoleControl]::GenerateConsoleCtrlEvent(1, [uint32]$instance.WrapperPid)
    [LuminaAuditConsoleControl]::FreeConsole() | Out-Null
    if (-not $sent) {
        throw "Ctrl+Break failed for verified wrapper $($instance.WrapperPid) (Win32 error $([Runtime.InteropServices.Marshal]::GetLastWin32Error())). No force-kill was attempted."
    }
    Wait-ForPortsFree @($instance.ServerPid, $instance.WrapperPid)
} elseif (-not (Test-PortsFree)) {
    throw 'A configured Lumina port remains occupied by an unidentified process; refusing to start a second instance.'
}

New-Item -ItemType Directory -Force -Path (Join-Path $repoRoot 'logs') | Out-Null
$env:LUMINA_MODULE_EXECUTION_AUDIT = '1'
$env:LUMINA_MODULE_AUDIT_OUTPUT = $profilePath
$env:LUMINA_SKIP_FRONTEND_BUILD = '1'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

Write-Output 'Starting exactly one audit instance through start.bat.'
$launcher = Start-Process -FilePath $env:ComSpec `
    -ArgumentList @('/d', '/c', 'call start.bat') `
    -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
Write-Output "Launcher PID: $($launcher.Id). Waiting up to ${StartupTimeoutSeconds}s for ready=true and /next/ HTTP 200."

$deadline = [DateTime]::UtcNow.AddSeconds($StartupTimeoutSeconds)
do {
    $ready = Test-LuminaReady
    if ($ready) {
        $ready | ConvertTo-Json -Depth 4
        exit 0
    }
    Start-Sleep -Seconds 2
} while ([DateTime]::UtcNow -lt $deadline)

$network = Get-LuminaListeners
throw "Lumina did not become HTTP-ready within ${StartupTimeoutSeconds}s. Listener PIDs: $($network.OwnerIds -join ', '). No second launch or force-kill was attempted. Inspect $stdoutPath and $stderrPath."
