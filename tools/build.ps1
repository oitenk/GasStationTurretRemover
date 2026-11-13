# Builds both editions of the mod. For each edition (base-game, phantom-liberty) it
# converts the JSON in source\<edition>\ to game files, checks that they read back
# identical to the sources, packs <edition>\archive\pc\mod\GasStationTurretRemover.archive
# and writes the edition's release zip to dist\.
#
# Phantom Liberty ships its own copies of the two world sectors with the turrets at
# other node indices, so each edition has its own .archive.xl (written by
# tools\make_sources.py) and its own quest sector.
#
# Game version 2.5 changed the world sector format, and the released WolvenKit CLI cannot
# read it yet, so the JSON is converted with tools\wkjson (built on the WolvenKit 10
# libraries). The CLI only packs the archive.
#
# usage: powershell -ExecutionPolicy Bypass -File tools\build.ps1
#            [-WolvenKit <path to WolvenKit.CLI.exe>] [-WolvenKitLibs <WolvenKit 10 folder>]
param(
    [string]$WolvenKit = 'D:\WolvenKit.Console-9.1.1\WolvenKit.CLI.exe',
    [string]$WolvenKitLibs = "$env:USERPROFILE\Downloads\WolvenKit-10.0.0-beta.1"
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$name = 'GasStationTurretRemover'
$work = Join-Path ([IO.Path]::GetTempPath()) "$name-build"
$editions = [ordered]@{ 'phantom-liberty' = 'PhantomLiberty'; 'base-game' = 'BaseGame' }

function Invoke-WolvenKit {
    & $WolvenKit @args | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "WolvenKit.CLI $($args[0]) failed" }
}

function Invoke-WkJson {
    & dotnet $wkjson @args | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "wkjson $($args[0]) $($args[1]) failed" }
}

if (-not (Test-Path $WolvenKit)) { throw "WolvenKit.CLI not found at $WolvenKit" }
if (-not (Test-Path (Join-Path $WolvenKitLibs 'WolvenKit.RED4.dll'))) { throw "WolvenKit 10 libraries not found in $WolvenKitLibs" }
if (Test-Path $work) { Remove-Item -Recurse -Force $work }

# Build the JSON converter.
$wkjsonDir = Join-Path $work 'wkjson'
& dotnet build (Join-Path $PSScriptRoot 'wkjson\wkjson.csproj') -c Release -o $wkjsonDir "-p:WolvenKitDir=$WolvenKitLibs" | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'building tools\wkjson failed' }
Copy-Item (Join-Path $WolvenKitLibs '*.dll') $wkjsonDir -ErrorAction SilentlyContinue
$wkjson = Join-Path $wkjsonDir 'wkjson.dll'

$dist = Join-Path $root 'dist'
New-Item -ItemType Directory -Force $dist | Out-Null

foreach ($edition in $editions.Keys) {
    $sourceDir = Join-Path $root "source\$edition"
    $modDir = Join-Path $root "$edition\archive\pc\mod"
    $editionWork = Join-Path $work $edition

    # JSON sources -> game files, in a folder named after the archive.
    $stage = Join-Path $editionWork $name
    $sources = Get-ChildItem -Recurse -File $sourceDir -Filter *.json
    foreach ($src in $sources) {
        $rel = $src.DirectoryName.Substring($sourceDir.Length).TrimStart('\')
        $dest = Join-Path $stage $rel
        New-Item -ItemType Directory -Force $dest | Out-Null
        Invoke-WkJson write $src.FullName (Join-Path $dest $src.BaseName)
    }

    # Read the game files back and compare them with the sources.
    $readBack = Join-Path $editionWork 'readback'
    New-Item -ItemType Directory -Force $readBack | Out-Null
    foreach ($src in $sources) {
        $rel = $src.DirectoryName.Substring($sourceDir.Length).TrimStart('\')
        $built = Join-Path (Join-Path $stage $rel) $src.BaseName
        Invoke-WkJson read $built (Join-Path $readBack $src.Name)
        & python (Join-Path $PSScriptRoot 'compare_json.py') $src.FullName (Join-Path $readBack $src.Name)
        if ($LASTEXITCODE -ne 0) { throw "$edition $($src.Name) does not read back identical" }
    }

    # Pack the archive.
    Invoke-WolvenKit pack $stage -o $editionWork
    New-Item -ItemType Directory -Force $modDir | Out-Null
    Copy-Item -Force (Join-Path $editionWork "$name.archive") (Join-Path $modDir "$name.archive")
    Write-Host "Built $(Join-Path $modDir "$name.archive")"

    # Release zip, laid out from the game root.
    $zip = Join-Path $dist "$name-$($editions[$edition]).zip"
    & python (Join-Path $PSScriptRoot 'make_zip.py') $zip (Join-Path $root $edition) "archive\pc\mod\$name.archive" "archive\pc\mod\$name.archive.xl"
    if ($LASTEXITCODE -ne 0) { throw 'writing the zip failed' }
    Write-Host "Built $zip"
}

Remove-Item -Recurse -Force $work
