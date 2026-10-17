# Builds archive\pc\mod\GasStationTurretRemover.archive from the JSON in source\,
# checks that the packed files read back identical to the sources, and writes the
# release zip to dist\.
#
# usage: powershell -ExecutionPolicy Bypass -File tools\build.ps1 [-WolvenKit <path to WolvenKit.CLI.exe>]
param(
    [string]$WolvenKit = 'D:\WolvenKit.Console-9.1.0\WolvenKit.CLI.exe'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$name = 'GasStationTurretRemover'
$modDir = Join-Path $root 'archive\pc\mod'
$work = Join-Path ([IO.Path]::GetTempPath()) "$name-build"

function Invoke-WolvenKit {
    & $WolvenKit @args | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "WolvenKit.CLI $($args[0]) failed" }
}

if (-not (Test-Path $WolvenKit)) { throw "WolvenKit.CLI not found at $WolvenKit" }
if (Test-Path $work) { Remove-Item -Recurse -Force $work }

# JSON sources -> game files, in a folder named after the archive.
$stage = Join-Path $work $name
$sources = Get-ChildItem -Recurse -File (Join-Path $root 'source') -Filter *.json
foreach ($src in $sources) {
    $rel = $src.DirectoryName.Substring((Join-Path $root 'source').Length).TrimStart('\')
    $dest = Join-Path $stage $rel
    New-Item -ItemType Directory -Force $dest | Out-Null
    Invoke-WolvenKit convert deserialize $src.FullName -o $dest
}

# Read the game files back and compare them with the sources.
$readBack = Join-Path $work 'readback'
New-Item -ItemType Directory -Force $readBack | Out-Null
foreach ($src in $sources) {
    $rel = $src.DirectoryName.Substring((Join-Path $root 'source').Length).TrimStart('\')
    $built = Join-Path (Join-Path $stage $rel) $src.BaseName
    Invoke-WolvenKit convert serialize $built -o $readBack
    & python (Join-Path $PSScriptRoot 'compare_json.py') $src.FullName (Join-Path $readBack $src.Name)
    if ($LASTEXITCODE -ne 0) { throw "$($src.Name) does not read back identical" }
}

# Pack the archive.
Invoke-WolvenKit pack $stage -o $work
Copy-Item -Force (Join-Path $work "$name.archive") (Join-Path $modDir "$name.archive")
Write-Host "Built $(Join-Path $modDir "$name.archive")"

# Release zip, laid out from the game root.
$dist = Join-Path $root 'dist'
New-Item -ItemType Directory -Force $dist | Out-Null
$zip = Join-Path $dist "$name.zip"
& python (Join-Path $PSScriptRoot 'make_zip.py') $zip $root "archive\pc\mod\$name.archive" "archive\pc\mod\$name.archive.xl"
if ($LASTEXITCODE -ne 0) { throw 'writing the zip failed' }
Write-Host "Built $zip"

Remove-Item -Recurse -Force $work
