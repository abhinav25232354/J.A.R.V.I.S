$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$bin = Join-Path $env:LOCALAPPDATA 'Programs\Jarvis\bin'
$venvPath = Join-Path $repo '.venv'
$venvPython = Join-Path $venvPath 'Scripts\python.exe'
$log = Join-Path $env:TEMP 'jarvis-setup.log'
$python = $null
$pythonArgs = @()

function Write-ProgressStep([int]$number, [int]$total, [string]$message) {
    Write-Host "Progress $number/$total`: $message"
}

function Stop-Setup([string]$message) {
    throw [System.InvalidOperationException]::new($message)
}

function Invoke-NativeLogged([string]$executable, [string[]]$arguments) {
    Remove-Item -LiteralPath $log -Force -ErrorAction SilentlyContinue
    try {
        & $executable @arguments *> $log
        return $LASTEXITCODE
    } catch {
        "The installer could not start the required command." | Set-Content -LiteralPath $log
        return 127
    }
}

function Test-PythonVersion([string]$executable, [string[]]$arguments) {
    try {
        $output = (& $executable @arguments --version 2>&1 | Out-String)
        if ($LASTEXITCODE -ne 0) { return $false }
        $match = [regex]::Match($output, 'Python\s+(\d+)\.(\d+)')
        if (-not $match.Success) { return $false }
        return ([int]$match.Groups[1].Value -gt 3 -or
            ([int]$match.Groups[1].Value -eq 3 -and [int]$match.Groups[2].Value -ge 10))
    } catch {
        return $false
    }
}

function Find-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        if (Test-PythonVersion 'py' @('-3')) { return @{ Executable = 'py'; Arguments = @('-3') } }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        if (Test-PythonVersion 'python' @()) { return @{ Executable = 'python'; Arguments = @() } }
    }
    return $null
}

function Find-WindowsOllama {
    $command = Get-Command ollama -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    foreach ($candidate in @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'),
        (Join-Path $env:LOCALAPPDATA 'Ollama\ollama.exe'),
        (Join-Path $env:ProgramFiles 'Ollama\ollama.exe')
    )) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    foreach ($registryPath in @(
        'Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\App Paths\ollama.exe',
        'Registry::HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\App Paths\ollama.exe'
    )) {
        try {
            $registered = (Get-Item -LiteralPath $registryPath).GetValue('')
            if ($registered -and (Test-Path -LiteralPath $registered)) { return $registered }
        } catch { }
    }
    return $null
}

function Find-WslOllama {
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) { return $null }
    try {
        $listing = & wsl.exe --list --quiet 2>$null
        if ($LASTEXITCODE -ne 0) { return $null }
        $listingText = ($listing -join "`n").Replace([string][char]0, '')
        $distros = @($listingText -split "`r?`n" | ForEach-Object { $_.Trim().TrimStart([char]'*').Trim() } | Where-Object { $_ })
        foreach ($distro in $distros) {
            $found = & wsl.exe -d $distro -- sh -lc 'command -v ollama' 2>$null
            $exitCode = $LASTEXITCODE
            $commandPath = ($found -join "`n").Trim()
            if ($exitCode -eq 0 -and $commandPath) {
                return @{ Distro = $distro; Path = $commandPath }
            }
        }
    } catch { return $null }
    return $null
}

try {
    Write-ProgressStep 1 8 'Checking prerequisites'
    $pythonInfo = Find-Python
    if (-not $pythonInfo) {
        if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
            Stop-Setup 'Python 3.10 or newer is required. Install Python or Windows Package Manager, then run setup again.'
        }
        Write-ProgressStep 2 8 'Installing Python runtime'
        if ((Invoke-NativeLogged 'winget' @('install', '--id', 'Python.Python.3.12', '--exact', '--silent', '--scope', 'user', '--accept-package-agreements', '--accept-source-agreements')) -ne 0) {
            Stop-Setup "Python could not be installed. Review the setup notes in $log and try again."
        }
        $pythonInfo = Find-Python
        if (-not $pythonInfo) {
            $candidate = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
            if (Test-Path -LiteralPath $candidate) { $pythonInfo = @{ Executable = $candidate; Arguments = @() } }
        }
        if (-not $pythonInfo -or -not (Test-PythonVersion $pythonInfo.Executable $pythonInfo.Arguments)) {
            Stop-Setup 'Python was installed but is not available yet. Open a new terminal and run setup again.'
        }
    } else {
        Write-ProgressStep 2 8 'Using installed Python'
    }
    $python = $pythonInfo.Executable
    $pythonArgs = @($pythonInfo.Arguments)

    Write-ProgressStep 3 8 'Choosing Ollama setup'
    Write-Host 'Ollama setup options:'
    Write-Host '  1. Install Ollama for Windows'
    Write-Host '  2. Ollama is already installed'
    do { $ollamaChoice = (Read-Host 'Choose 1 or 2').Trim() } while ($ollamaChoice -notin @('1', '2'))

    if ($ollamaChoice -eq '1') {
        $ollamaTarget = 'Windows'
        Write-ProgressStep 4 8 'Installing Windows Ollama'
        if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
            Stop-Setup 'Windows Package Manager is required for automatic Ollama installation. Install Ollama manually, then rerun setup.'
        }
        if ((Invoke-NativeLogged 'winget' @('install', '--id', 'Ollama.Ollama', '--exact', '--silent', '--accept-package-agreements', '--accept-source-agreements')) -ne 0) {
            Stop-Setup "Ollama could not be installed. Review the setup notes in $log and install it from ollama.com/download."
        }
        if (-not (Find-WindowsOllama)) {
            Stop-Setup 'Ollama was installed but Windows cannot locate its command yet. Open a new terminal and run setup again.'
        }
    } else {
        Write-Host 'Where is Ollama installed?'
        Write-Host '  1. Windows'
        Write-Host '  2. WSL'
        do { $ollamaLocation = (Read-Host 'Choose 1 or 2').Trim() } while ($ollamaLocation -notin @('1', '2'))
        if ($ollamaLocation -eq '1') {
            $ollamaTarget = 'Windows'
            Write-ProgressStep 4 8 'Checking Windows Ollama'
            if (-not (Find-WindowsOllama)) {
                Stop-Setup 'Ollama was not found in Windows. Choose WSL if it is installed there, or rerun setup and select installation.'
            }
            Write-Host 'Ollama was found in Windows.'
        } else {
            $ollamaTarget = 'WSL'
            Write-ProgressStep 4 8 'Checking WSL Ollama'
            $wslOllama = Find-WslOllama
            if (-not $wslOllama) {
                Stop-Setup 'Ollama was not found in any WSL distribution. Install it in WSL or rerun setup and choose Windows installation.'
            }
            Write-Host "Ollama was found in WSL distribution: $($wslOllama.Distro)."
            $ollamaDistro = $wslOllama.Distro
        }
    }

    Write-ProgressStep 5 8 'Preparing Python environment'
    if (Test-Path -LiteralPath $venvPath) {
        $resolvedVenv = (Resolve-Path -LiteralPath $venvPath).Path
        if ([IO.Path]::GetFullPath($resolvedVenv) -ne [IO.Path]::GetFullPath($venvPath) -or (Split-Path -Parent $resolvedVenv) -ne $repo) {
            Stop-Setup 'The existing Python environment path is unexpected. Move it aside and run setup again.'
        }
    }
    $venvArguments = @($pythonArgs) + @('-m', 'venv', '--upgrade', $venvPath)
    if ((Invoke-NativeLogged $python $venvArguments) -ne 0 -or -not (Test-Path -LiteralPath $venvPython)) {
        Stop-Setup "The private Python environment could not be prepared. Review the setup notes in $log."
    }
    if (-not (Test-PythonVersion $venvPython @())) {
        Stop-Setup 'The private environment uses an unsupported Python version. Update Python and run setup again.'
    }

    Write-ProgressStep 6 8 'Installing Python libraries'
    if ((Invoke-NativeLogged $venvPython @('-m', 'ensurepip', '--upgrade')) -ne 0) {
        Stop-Setup "Python package support could not be prepared. Review the setup notes in $log."
    }
    if ((Invoke-NativeLogged $venvPython @('-m', 'pip', 'install', '--upgrade', '--disable-pip-version-check', 'pip', 'setuptools', 'wheel')) -ne 0) {
        Stop-Setup "Python package tools could not be updated. Check your connection and review $log."
    }
    if ((Invoke-NativeLogged $venvPython @('-m', 'pip', 'install', '--upgrade', '--disable-pip-version-check', '-r', (Join-Path $repo 'requirements.txt'))) -ne 0) {
        Stop-Setup "Jarvis libraries could not be installed. Check your connection and review $log."
    }
    if ((Invoke-NativeLogged $venvPython @('-m', 'pip', 'check')) -ne 0) {
        Stop-Setup "Some Python libraries have incompatible requirements. Review $log and run setup again."
    }
    Write-ProgressStep 7 8 'Updating Jarvis command'
    New-Item -ItemType Directory -Force -Path $bin | Out-Null
    $launcher = Join-Path $bin 'jarvis.cmd'
    @"
@echo off
"$venvPython" "$repo\main.py" %*
"@ | Set-Content -LiteralPath $launcher -Encoding Ascii

    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $entries = @($userPath -split ';' | Where-Object { $_ })
    if (-not ($entries | Where-Object { $_.TrimEnd('\') -ieq $bin.TrimEnd('\') })) {
        [Environment]::SetEnvironmentVariable('Path', ((@($entries) + $bin) -join ';'), 'User')
    }
    if (-not (($env:Path -split ';') | Where-Object { $_.TrimEnd('\') -ieq $bin.TrimEnd('\') })) { $env:Path += ";$bin" }

    $profilePath = $PROFILE.CurrentUserCurrentHost
    $profileDirectory = Split-Path -Parent $profilePath
    New-Item -ItemType Directory -Force -Path $profileDirectory | Out-Null
    $pythonLiteral = "'" + $venvPython.Replace("'", "''") + "'"
    $scriptLiteral = "'" + (Join-Path $repo 'main.py').Replace("'", "''") + "'"
    $functionDefinition = 'function jarvis { & ' + $pythonLiteral + ' ' + $scriptLiteral + ' @args }'
    $profileText = if (Test-Path -LiteralPath $profilePath) { Get-Content -LiteralPath $profilePath -Raw } else { '' }
    $profileText = [regex]::Replace($profileText, '(?ms)^# Jarvis CLI function BEGIN\r?\n.*?^# Jarvis CLI function END\r?\n?', '')
    $profileText = [regex]::Replace($profileText, '(?m)^# Jarvis CLI function\r?\nfunction jarvis \{.*\}\r?\n?', '')
    $profileBlock = "# Jarvis CLI function BEGIN`n$functionDefinition`n# Jarvis CLI function END`n"
    Set-Content -LiteralPath $profilePath -Value ($profileText.TrimEnd() + "`n`n" + $profileBlock) -Encoding UTF8

    Write-ProgressStep 8 8 'Finishing installation'
    Remove-Item -LiteralPath $log -Force -ErrorAction SilentlyContinue
    Write-Host 'Jarvis is installed or updated. Open a new terminal and type: jarvis'
    if ($ollamaTarget -eq 'WSL') {
        Write-Host "Setup note: In WSL ($ollamaDistro), install a model with: ollama pull llama3.2"
    } else {
        Write-Host 'Setup note: Install a model with: ollama pull llama3.2'
    }
} catch {
    if ($_.Exception -is [System.InvalidOperationException]) {
        $friendlyError = $_.Exception.Message
    } else {
        $friendlyError = 'An unexpected setup issue occurred. Check permissions, available disk space, and network access.'
        try { $_ | Out-String | Set-Content -LiteralPath $log -Encoding UTF8 } catch { }
    }
    Write-Host "Setup could not finish: $friendlyError" -ForegroundColor Red
    if (Test-Path -LiteralPath $log) { Write-Host "Setup notes were saved to: $log" }
    exit 1
}
