# Papyrus Windows Setup Script
# This script automates the installation and configuration of Papyrus on Windows
# Usage: powershell -ExecutionPolicy Bypass -File setup-windows.ps1

param(
    [switch]$SkipTesseract = $false,
    [string]$TesseractPath = ""
)

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "=" * 60
    Write-Host $Text
    Write-Host "=" * 60
}

function Write-Success {
    param([string]$Text)
    Write-Host "✓ $Text" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Text)
    Write-Host "✗ $Text" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Text)
    Write-Host "⚠ $Text" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Text)
    Write-Host "ℹ $Text" -ForegroundColor Cyan
}

# Check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Find Tesseract installation
function Find-Tesseract {
    param([string]$ProvidedPath)

    if ($ProvidedPath -and (Test-Path "$ProvidedPath\tesseract.exe")) {
        Write-Success "Found Tesseract at: $ProvidedPath"
        return $ProvidedPath
    }

    $commonPaths = @(
        "C:\Program Files\Tesseract-OCR",
        "C:\Program Files (x86)\Tesseract-OCR",
        "$env:USERPROFILE\Tesseract-OCR",
        "C:\Tesseract-OCR"
    )

    Write-Info "Searching for Tesseract installation..."

    foreach ($path in $commonPaths) {
        if (Test-Path "$path\tesseract.exe") {
            Write-Success "Found Tesseract at: $path"
            return $path
        }
    }

    return $null
}

# Download and install Tesseract
function Install-Tesseract {
    Write-Header "Installing Tesseract OCR"

    Write-Info "This script will download and install Tesseract-OCR v5"
    Write-Info "You can also manually download from: https://github.com/UB-Mannheim/tesseract/wiki"

    $installerUrl = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w64-setup-v5.3.3.exe"
    $installerPath = "$env:TEMP\tesseract-installer.exe"

    try {
        Write-Info "Downloading Tesseract installer (~150MB)..."
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
        Write-Success "Downloaded Tesseract installer"

        Write-Info "Running Tesseract installer..."
        Write-Info "Please complete the installation wizard (default path is fine)"
        Start-Process $installerPath -Wait

        Write-Info "Waiting for installation to complete..."
        Start-Sleep -Seconds 3

        # Try to find the newly installed Tesseract
        $tesseractPath = Find-Tesseract -ProvidedPath ""
        if ($tesseractPath) {
            Write-Success "Tesseract installed successfully at: $tesseractPath"
            return $tesseractPath
        } else {
            Write-Error-Custom "Could not find Tesseract after installation"
            Write-Info "Please ensure you installed Tesseract and try again"
            return $null
        }
    }
    catch {
        Write-Error-Custom "Failed to download/install Tesseract: $_"
        Write-Info "You can manually download from: https://github.com/UB-Mannheim/tesseract/wiki"
        return $null
    }
}

# Set environment variable
function Set-TesseractEnv {
    param([string]$TesseractPath)

    Write-Header "Configuring Environment Variables"

    if (-not (Test-Administrator)) {
        Write-Warning-Custom "This step requires administrator privileges"
        Write-Info "Please run this script as Administrator to set permanent environment variables"
        Write-Info "You can still set TESSERACT_CMD in your PowerShell profile manually:"
        Write-Host "`$env:TESSERACT_CMD = '$TesseractPath\tesseract.exe'" -ForegroundColor Yellow
        return $false
    }

    try {
        Write-Info "Setting TESSERACT_CMD environment variable..."
        [Environment]::SetEnvironmentVariable(
            "TESSERACT_CMD",
            "$TesseractPath\tesseract.exe",
            [EnvironmentVariableTarget]::User
        )
        Write-Success "Environment variable set permanently for current user"

        # Also set for current session
        $env:TESSERACT_CMD = "$TesseractPath\tesseract.exe"
        Write-Success "Environment variable set for current session"

        return $true
    }
    catch {
        Write-Error-Custom "Failed to set environment variable: $_"
        return $false
    }
}

# Install Papyrus
function Install-Papyrus {
    Write-Header "Installing Papyrus"

    $script_dir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $venv_path = "$script_dir\venv"

    try {
        if (-not (Test-Path $venv_path)) {
            Write-Info "Creating Python virtual environment..."
            python -m venv venv
            Write-Success "Virtual environment created"
        }

        Write-Info "Activating virtual environment..."
        & "$venv_path\Scripts\Activate.ps1"
        Write-Success "Virtual environment activated"

        Write-Info "Installing Papyrus and dependencies..."
        pip install -e .
        Write-Success "Papyrus installed successfully"

        return $true
    }
    catch {
        Write-Error-Custom "Failed to install Papyrus: $_"
        return $false
    }
}

# Test installation
function Test-Installation {
    Write-Header "Testing Installation"

    try {
        Write-Info "Testing papyrus command..."
        $output = & papyrus --help

        if ($LASTEXITCODE -eq 0) {
            Write-Success "papyrus command works correctly"
            return $true
        } else {
            Write-Warning-Custom "papyrus command returned an error"
            Write-Info "Please restart your terminal and try again"
            return $false
        }
    }
    catch {
        Write-Error-Custom "Failed to test papyrus: $_"
        Write-Info "Please restart your terminal and try again"
        return $false
    }
}

# Add to PATH (optional)
function Add-ToPATH {
    param([string]$PapyrusPath)

    Write-Header "Adding Papyrus to PATH (Optional)"

    Write-Info "Do you want to add Papyrus to your system PATH?"
    Write-Info "This allows you to run 'papyrus' from any directory without activating venv"

    $response = Read-Host "Add to PATH? (Y/n)"

    if ($response -ne "n") {
        if (-not (Test-Administrator)) {
            Write-Warning-Custom "Adding to PATH requires administrator privileges"
            Write-Info "Please run this script as Administrator, or manually add:"
            Write-Host "$PapyrusPath\venv\Scripts" -ForegroundColor Yellow
            return $false
        }

        try {
            $venvBinPath = "$PapyrusPath\venv\Scripts"
            $currentPath = [Environment]::GetEnvironmentVariable("PATH", [EnvironmentVariableTarget]::User)

            if ($currentPath -notlike "*$venvBinPath*") {
                $newPath = "$currentPath;$venvBinPath"
                [Environment]::SetEnvironmentVariable(
                    "PATH",
                    $newPath,
                    [EnvironmentVariableTarget]::User
                )
                Write-Success "Added Papyrus to PATH"
                Write-Info "Please restart your terminal for changes to take effect"
            } else {
                Write-Success "Papyrus is already in PATH"
            }
            return $true
        }
        catch {
            Write-Error-Custom "Failed to add to PATH: $_"
            return $false
        }
    }

    return $false
}

# Main setup flow
function Main {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║           Papyrus Windows Setup Script                   ║" -ForegroundColor Cyan
    Write-Host "║  Universal Document Parser for AI Agents                 ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    # Step 1: Check/Install Tesseract
    if ($SkipTesseract) {
        Write-Info "Skipping Tesseract check (as requested)"
        $tesseractPath = $null
    } else {
        $tesseractPath = Find-Tesseract -ProvidedPath $TesseractPath

        if (-not $tesseractPath) {
            Write-Warning-Custom "Tesseract not found"
            $response = Read-Host "Download and install Tesseract? (Y/n)"

            if ($response -ne "n") {
                $tesseractPath = Install-Tesseract
                if (-not $tesseractPath) {
                    Write-Error-Custom "Cannot continue without Tesseract"
                    return
                }
            }
        }
    }

    # Step 2: Set environment variable
    if ($tesseractPath) {
        Set-TesseractEnv -TesseractPath $tesseractPath
    }

    # Step 3: Install Papyrus
    $script_dir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $installed = Install-Papyrus

    if (-not $installed) {
        Write-Error-Custom "Installation failed. Please check the errors above."
        return
    }

    # Step 4: Test installation
    $tested = Test-Installation

    # Step 5: Add to PATH (optional)
    Add-ToPATH -PapyrusPath $script_dir

    # Summary
    Write-Header "Setup Complete!"

    if ($tested) {
        Write-Success "Papyrus is ready to use!"
        Write-Host ""
        Write-Info "Try these commands:"
        Write-Host "  papyrus --help              # Show help"
        Write-Host "  papyrus document.pdf        # Parse a PDF"
        Write-Host "  papyrus slides.pptx --format json  # Parse PowerPoint as JSON"
        Write-Host ""
    } else {
        Write-Warning-Custom "Setup completed but testing failed"
        Write-Info "Please restart your terminal and try again"
        Write-Info "If you manually set PATH, make sure to restart your terminal"
    }

    Write-Host ""
}

# Run main setup
Main
