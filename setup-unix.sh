#!/bin/bash

# Papyrus Unix Setup Script (macOS and Linux)
# This script automates the installation and configuration of Papyrus
# Usage: bash setup-unix.sh

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo ""
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Tesseract for macOS
install_tesseract_macos() {
    print_header "Installing Tesseract (macOS)"

    if command_exists brew; then
        print_info "Using Homebrew to install Tesseract..."
        brew install tesseract
        print_success "Tesseract installed via Homebrew"
        return 0
    else
        print_error "Homebrew not found"
        print_info "Please install Homebrew from: https://brew.sh"
        print_info "Then run this script again"
        return 1
    fi
}

# Install Tesseract for Linux
install_tesseract_linux() {
    print_header "Installing Tesseract (Linux)"

    if command_exists apt-get; then
        print_info "Using apt to install Tesseract and dependencies..."
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr libmagic1
        print_success "Tesseract and dependencies installed"
        return 0
    elif command_exists yum; then
        print_info "Using yum to install Tesseract..."
        sudo yum install -y tesseract libmagic
        print_success "Tesseract and dependencies installed"
        return 0
    elif command_exists pacman; then
        print_info "Using pacman to install Tesseract..."
        sudo pacman -S tesseract
        print_success "Tesseract installed"
        return 0
    else
        print_error "Package manager not found"
        print_info "Please install Tesseract manually from: https://github.com/UB-Mannheim/tesseract/wiki"
        return 1
    fi
}

# Check python3-venv availability
 check_python3_venv() {
     print_info "Checking python3-venv support..."
     if python3 -m venv --help >/dev/null 2>&1; then
         return 0
     fi
     print_error "python3-venv is not available"
     print_info "Ubuntu/Debian: sudo apt-get install -y python3-venv"
     print_info "Other distros: install the python3-venv package for your distribution"
     return 1
 }

# Install Papyrus
install_papyrus() {
    print_header "Installing Papyrus"

    local script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    local venv_path="$script_dir/venv"

    if [ ! -d "$venv_path" ]; then
        if ! check_python3_venv; then
            return 1
        fi
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    fi

    print_info "Activating virtual environment..."
    source "$venv_path/bin/activate"
    print_success "Virtual environment activated"

    print_info "Installing Papyrus and dependencies..."
    pip install --upgrade pip setuptools wheel
    pip install -e .
    print_success "Papyrus installed successfully"

    return 0
}

# Test installation
test_installation() {
    print_header "Testing Installation"

    print_info "Testing papyrus command..."
    if papyrus --help >/dev/null 2>&1; then
        print_success "papyrus command works correctly"
        return 0
    else
        print_warning "papyrus command test failed"
        print_info "Try reloading your shell: source ~/.zshrc or source ~/.bashrc"
        return 1
    fi
}

# Add to PATH
add_to_path() {
    print_header "Adding Papyrus to PATH (Optional)"

    local script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    local venv_bin="$script_dir/venv/bin"

    print_info "Do you want to add Papyrus to your system PATH?"
    print_info "This allows running 'papyrus' from any directory without activating venv"
    read -p "Add to PATH? (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ "$SHELL" == *"zsh"* ]]; then
            local shell_rc="$HOME/.zshrc"
        else
            local shell_rc="$HOME/.bashrc"
        fi

        local path_export="export PATH=\"\$HOME/papyrus/venv/bin:\$PATH\""

        if grep -q "papyrus/venv/bin" "$shell_rc"; then
            print_success "Papyrus is already in PATH"
        else
            echo "" >> "$shell_rc"
            echo "# papyrus: universal document parser" >> "$shell_rc"
            echo "$path_export" >> "$shell_rc"
            print_success "Added to $shell_rc"
            print_info "Reload your shell to apply changes: source $shell_rc"
        fi
    fi
}

# Main installation flow
main() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           Papyrus Unix Setup Script                      ║${NC}"
    echo -e "${CYAN}║  Universal Document Parser for AI Agents                 ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    local os=$(detect_os)

    if [ "$os" = "unknown" ]; then
        print_error "Unknown operating system"
        exit 1
    fi

    print_info "Detected OS: $(echo $os | tr '[:lower:]' '[:upper:]')"

    # Step 1: Install Tesseract
    if [ "$os" = "macos" ]; then
        if ! install_tesseract_macos; then
            print_warning "Tesseract installation skipped"
        fi
    else
        if ! install_tesseract_linux; then
            print_warning "Tesseract installation skipped"
        fi
    fi

    # Step 2: Install Papyrus
    if ! install_papyrus; then
        print_error "Installation failed. Please check the errors above."
        exit 1
    fi

    # Step 3: Test installation
    local test_passed=1
    if test_installation; then
        test_passed=0
    fi

    # Step 4: Add to PATH
    add_to_path

    # Summary
    print_header "Setup Complete!"

    if [ $test_passed -eq 0 ]; then
        print_success "Papyrus is ready to use!"
        echo ""
        print_info "Try these commands:"
        echo "  papyrus --help              # Show help"
        echo "  papyrus document.pdf        # Parse a PDF"
        echo "  papyrus slides.pptx --format json  # Parse PowerPoint as JSON"
        echo ""
    else
        print_warning "Setup completed but testing failed"
        print_info "Try reloading your shell:"
        if [[ "$SHELL" == *"zsh"* ]]; then
            echo "  source ~/.zshrc"
        else
            echo "  source ~/.bashrc"
        fi
    fi

    echo ""
}

# Run main setup
main "$@"
