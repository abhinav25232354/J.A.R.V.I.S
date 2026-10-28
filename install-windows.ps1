$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path $PSScriptRoot).Path
$bin = Join-Path $env:LOCALAPPDATA 'Programs\Jarvis\bin'
New-Item -ItemType Directory -Force -Path $bin | Out-Null
$launcher = Join-Path $bin 'jarvis.cmd'
@"
@echo off
python "$repo\main.py" %*
"@ | Set-Content -LiteralPath $launcher -Encoding Ascii

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$entries = @($userPath -split ';' | Where-Object { $_ })
if ($entries -notcontains $bin) {
    $newPath = (@($entries) + $bin) -join ';'
    [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
    $env:Path += ";$bin"
}
Write-Host "Installed 'jarvis' at $launcher"
Write-Host 'Open a new terminal, then type: jarvis'
