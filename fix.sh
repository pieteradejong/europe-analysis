#!/bin/bash

# Exit on error
set -e

# Function to print section headers
print_section() {
    echo ""
    echo "=== $1 ==="
    echo ""
}

# Activate virtual environment
source venv/bin/activate

print_section "🔧 Auto-fixing Code Issues"

# 1. Ruff auto-fix
print_section "Ruff Auto-fix"
ruff check --fix backend/

# 2. Black formatting
print_section "Black Formatting"
black backend/

# 3. Run linting again to check
print_section "Verification"
ruff check backend/
black --check backend/

print_section "✅ All Issues Fixed"
echo "Run './lint.sh' to verify everything passes" 