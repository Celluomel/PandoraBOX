param(
    [string]$OpenSCAD = "C:\Program Files\OpenSCAD\openscad.exe",
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"
$source = Join-Path $PSScriptRoot "hexapode_chassis_ventuno_q_light.scad"
if (-not $OutputDir) {
    $OutputDir = Join-Path (Split-Path $PSScriptRoot -Parent | Split-Path -Parent) "artifacts\hexapode_chassis\ender3_kit"
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
if (-not (Test-Path -LiteralPath $OpenSCAD)) {
    throw "OpenSCAD CLI not found at '$OpenSCAD'. Pass -OpenSCAD with the path to openscad.com."
}

$parts = @(
    "lower_front", "lower_center", "lower_rear",
    "upper_front", "upper_center", "upper_rear",
    "lower_joiner", "upper_joiner",
    "spacer", "us_mount", "radar_tower", "lidar_mast", "imu_pad", "gps_mast", "tof_mount"
)

function Export-Part([string]$Part, [string]$Output, [bool]$Compact = $false) {
    $partValue = 'part=""' + $Part + '""'
    $arguments = '-o "' + $Output + '" -D "' + $partValue + '"'
    if ($Compact) { $arguments += ' -D compact_print=true' }
    $arguments += ' "' + $source + '"'
    $process = Start-Process -FilePath $OpenSCAD -ArgumentList $arguments -NoNewWindow -Wait -PassThru
    if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $Output)) {
        throw "OpenSCAD failed to export '$Part' (exit $($process.ExitCode))."
    }
}

foreach ($part in $parts) {
    $output = Join-Path $OutputDir "$part.stl"
    Write-Host "Exporting $part..."
    Export-Part $part $output
}
Write-Host "STLs exported to $OutputDir"

$singlePieceDir = Join-Path $OutputDir "one_piece_205mm"
New-Item -ItemType Directory -Force -Path $singlePieceDir | Out-Null
foreach ($part in @("lower", "upper")) {
    $output = Join-Path $singlePieceDir "${part}_205mm.stl"
    Write-Host "Exporting compact one-piece $part deck (205 mm)..."
    Export-Part $part $output $true
}
Write-Host "One-piece deck STLs exported to $singlePieceDir"
