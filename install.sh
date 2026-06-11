#!/bin/bash
# Quick install script for Papyrus

set -e

echo "Installing Papyrus..."

# Detect Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Error: Python not found"
    exit 1
fi

echo "Using Python: $($PYTHON --version)"

# Install in editable mode
$PYTHON -m pip install -e .

echo ""
echo "✅ Installation complete!"
echo ""
echo "Test it:"
echo "  papyrus --help"
echo ""
echo "Install heavy path support (optional):"
echo "  pip install 'papyrus[heavy]'"
