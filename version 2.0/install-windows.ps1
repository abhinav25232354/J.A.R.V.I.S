$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path $PSScriptRoot).Path
$bin = Join-Path $env:LOCALAPPDATA 'Programs\Jarvis\bin'
$venvPython = Join-Path $repo '.venv\Scripts\python.exe'

Write-Host 'Jarvis setup: checking Python...'
$python = $null
$pythonArgs = @()

function Test-PythonVersion($command, $arguments) {
    try {
        $output = (& $command @arguments --version 2>&1 | Out-String)
        if ($LASTEXITCODE -ne 0) { return $false }
        $match = [regex]::Match($output, 'Python\s+(\d+)\.(\d+)')
        if (-not $match.Success) { return $false }
        return ([int]$match.Groups[1].Value -gt 3 -or
            ([int]$match.Groups[1].Value -eq 3 -and [int]$match.Groups[2].Value -ge 10))
    } catch {
        return $false
    }
}

function Invoke-PythonQuiet($executable, [string[]]$arguments, $logPath) {
    $stdoutPath = "$logPath.stdout"
    $stderrPath = "$logPath.stderr"
    Remove-Item -LiteralPath $stdoutPath, $stderrPath -Force -ErrorAction SilentlyContinue
    $argumentLine = ($arguments | ForEach-Object { '"' + $_ + '"' }) -join ' '
    $process = Start-Process -FilePath $executable -ArgumentList $argumentLine -Wait -PassThru -NoNewWindow `
        -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    if ($process.ExitCode -ne 0) {
        $details = @()
        if (Test-Path $stdoutPath) { $details += Get-Content -LiteralPath $stdoutPath }
        if (Test-Path $stderrPath) { $details += Get-Content -LiteralPath $stderrPath }
        Set-Content -LiteralPath $logPath -Value $details
    } else {
        Remove-Item -LiteralPath $stdoutPath, $stderrPath -Force -ErrorAction SilentlyContinue
    }
    return $process.ExitCode
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    if (Test-PythonVersion 'py' @('-3')) {
        $python = 'py'
        $pythonArgs = @('-3')
    }
}
if (-not $python -and (Get-Command python -ErrorAction SilentlyContinue)) {
    if (Test-PythonVersion 'python' @()) { $python = 'python' }
}

if (-not $python) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw 'Python 3.10+ is required. Install winget or Python, then rerun this installer.'
    }
    Write-Host 'Installing Python 3.12...'
    & winget install --id Python.Python.3.12 --exact --silent --scope user --accept-package-agreements --accept-source-agreements *> $null
    if ($LASTEXITCODE -ne 0) { throw 'Python installation failed. Install Python 3.10+ and rerun this installer.' }
    $python = 'py'
    $pythonArgs = @('-3.12')
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
        $candidate = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
        if (Test-Path $candidate) { $python = $candidate; $pythonArgs = @() }
    }
    if (-not (Test-PythonVersion $python $pythonArgs)) {
        throw 'Python was installed but could not be located. Open a new terminal and rerun this installer.'
    }
}

Write-Host 'Preparing private environment...'
$log = Join-Path $env:TEMP 'jarvis-setup.log'
if (-not (Test-Path $venvPython)) {
    $venvPath = Join-Path $repo '.venv'
    $venvArgs = @($pythonArgs) + @('-m', 'venv', $venvPath)
    if ((Invoke-PythonQuiet $python $venvArgs $log) -ne 0) { throw "Python environment setup failed. Details: $log" }
}
Write-Host 'Installing required libraries...'
$pipArgs = @('-m', 'pip', 'install', '--disable-pip-version-check', '--quiet', '-r', (Join-Path $repo 'requirements.txt'))
if ((Invoke-PythonQuiet $venvPython $pipArgs $log) -ne 0) { throw "Library installation failed. Details: $log" }

New-Item -ItemType Directory -Force -Path $bin | Out-Null
$launcher = Join-Path $bin 'jarvis.cmd'
@"
@echo off
"$venvPython" "$repo\main.py" %*
"@ | Set-Content -LiteralPath $launcher -Encoding Ascii

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$entries = @($userPath -split ';' | Where-Object { $_ })
if ($entries -notcontains $bin) {
    [Environment]::SetEnvironmentVariable('Path', ((@($entries) + $bin) -join ';'), 'User')
}
$env:Path += ";$bin"

# Resolve `jarvis` as a PowerShell function in the same console, without shell
# file-association handling for the Python source file.
$profilePath = $PROFILE.CurrentUserCurrentHost
$profileDirectory = Split-Path -Parent $profilePath
New-Item -ItemType Directory -Force -Path $profileDirectory | Out-Null
$pythonLiteral = "'" + $venvPython.Replace("'", "''") + "'"
$scriptLiteral = "'" + (Join-Path $repo 'main.py').Replace("'", "''") + "'"
$profileMarker = '# Jarvis CLI function'
if (-not (Test-Path $profilePath) -or -not (Select-String -LiteralPath $profilePath -SimpleMatch $profileMarker -Quiet)) {
    $functionDefinition = 'function jarvis { & ' + $pythonLiteral + ' ' + $scriptLiteral + ' @args }'
    Add-Content -LiteralPath $profilePath -Encoding UTF8 -Value "`n$profileMarker`n$functionDefinition"
}
Write-Host 'Jarvis is installed. Open a terminal and type: jarvis'
