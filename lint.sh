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

print_section "🔍 Running Linting Suite"

# 1. Ruff linting
print_section "Ruff Linting"
ruff check backend/

# 2. Black formatting check
print_section "Black Formatting"
black --check backend/

# 3. Type checking (optional, can be slow)
if [ "${1:-}" = "--with-types" ]; then
    print_section "Type Checking"
    mypy --strict --ignore-missing-imports --explicit-package-bases backend/src backend/tests
fi

print_section "✅ All Linting Passed"
echo "To auto-fix issues, run:"
echo "  ruff check --fix backend/"
echo "  black backend/"
echo ""
echo "To run with type checking:"
echo "  ./lint.sh --with-types" 