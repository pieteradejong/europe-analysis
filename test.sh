#!/bin/bash

# Comprehensive Test Suite
# Runs linting, type checking, and tests for both backend and frontend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track results
LINT_BACKEND=0
LINT_FRONTEND=0
TYPECHECK=0
TEST_BACKEND=0
TEST_FRONTEND=0
TOTAL_FAILURES=0

# Parse arguments
QUICK=false
BACKEND_ONLY=false
FRONTEND_ONLY=false

for arg in "$@"; do
    case $arg in
        --quick)
            QUICK=true
            shift
            ;;
        --backend-only)
            BACKEND_ONLY=true
            shift
            ;;
        --frontend-only)
            FRONTEND_ONLY=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./test.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --quick          Skip linting and type checking"
            echo "  --backend-only   Run only backend tests"
            echo "  --frontend-only  Run only frontend tests"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
    esac
done

# Function to print section headers
print_section() {
    echo ""
    echo -e "${BLUE}=== $1 ===${NC}"
    echo ""
}

# Function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print failure
print_failure() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo ""
echo -e "${BLUE}=== 🧪 Comprehensive Test Suite ===${NC}"
echo ""

# Activate virtual environment for backend
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    print_success "Virtual environment activated"
else
    print_failure "Virtual environment not found. Run ./init.sh first."
    exit 1
fi

# ============================================
# DATABASE SETUP FOR TESTS
# ============================================
if [ "$FRONTEND_ONLY" = false ]; then
    print_section "🗄️  Database Setup"
    
    echo "Setting up test database..."
    # Use a separate test database
    export DATABASE_URL="sqlite:///backend/data/test_demographics.db"
    
    # Remove old test database for clean state
    rm -f backend/data/test_demographics.db
    
    # Ensure data directory exists
    mkdir -p backend/data
    
    # Run migrations on test database
    cd backend
    if python -m alembic upgrade head; then
        print_success "Test database migrations applied"
    else
        print_failure "Failed to apply test database migrations"
        exit 1
    fi
    cd ..
fi

# ============================================
# LINTING
# ============================================
if [ "$QUICK" = false ]; then
    print_section "🔍 Linting"

    # Backend linting
    if [ "$FRONTEND_ONLY" = false ]; then
        echo "Running backend linting (ruff + black)..."
        if ruff check backend/ && black --check backend/ 2>/dev/null; then
            print_success "Backend linting passed"
            LINT_BACKEND=1
        else
            print_failure "Backend linting failed"
            TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
        fi
    fi

    # Frontend linting
    if [ "$BACKEND_ONLY" = false ]; then
        echo ""
        echo "Running frontend linting (eslint)..."
        if (cd frontend && npm run lint 2>/dev/null); then
            print_success "Frontend linting passed"
            LINT_FRONTEND=1
        else
            print_failure "Frontend linting failed"
            TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
        fi
    fi
fi

# ============================================
# TYPE CHECKING
# ============================================
if [ "$QUICK" = false ] && [ "$FRONTEND_ONLY" = false ]; then
    print_section "🔬 Type Checking"

    echo "Running mypy on backend..."
    if mypy --strict --ignore-missing-imports --explicit-package-bases backend/src backend/tests 2>/dev/null; then
        print_success "Type checking passed"
        TYPECHECK=1
    else
        print_failure "Type checking failed"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
fi

# ============================================
# BACKEND TESTS
# ============================================
if [ "$FRONTEND_ONLY" = false ]; then
    print_section "🐍 Backend Tests (pytest)"

    echo "Running pytest with coverage..."
    if pytest backend/tests/ \
        --cov=backend/src \
        --cov-report=term-missing \
        --cov-report=html:backend/coverage_html \
        --cov-fail-under=0 \
        -v 2>&1; then
        print_success "Backend tests passed"
        TEST_BACKEND=1
        
        # Extract coverage percentage
        COVERAGE=$(pytest backend/tests/ --cov=backend/src --cov-report=term 2>&1 | grep "TOTAL" | awk '{print $NF}' | tr -d '%')
        if [ -n "$COVERAGE" ] && [ "$COVERAGE" -lt 70 ]; then
            print_warning "Backend coverage is ${COVERAGE}% (below 70% threshold)"
        fi
    else
        print_failure "Backend tests failed"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
fi

# ============================================
# FRONTEND TESTS
# ============================================
if [ "$BACKEND_ONLY" = false ]; then
    print_section "⚛️  Frontend Tests (vitest)"

    echo "Running vitest with coverage..."
    if (cd frontend && npm run test:coverage 2>&1); then
        print_success "Frontend tests passed"
        TEST_FRONTEND=1
    else
        print_failure "Frontend tests failed"
        TOTAL_FAILURES=$((TOTAL_FAILURES + 1))
    fi
fi

# ============================================
# SUMMARY
# ============================================
print_section "📊 Test Summary"

echo ""
echo "Results:"
echo "--------"

if [ "$QUICK" = false ]; then
    if [ "$FRONTEND_ONLY" = false ]; then
        if [ $LINT_BACKEND -eq 1 ]; then
            echo -e "  Backend Linting:    ${GREEN}PASSED${NC}"
        else
            echo -e "  Backend Linting:    ${RED}FAILED${NC}"
        fi
    fi

    if [ "$BACKEND_ONLY" = false ]; then
        if [ $LINT_FRONTEND -eq 1 ]; then
            echo -e "  Frontend Linting:   ${GREEN}PASSED${NC}"
        else
            echo -e "  Frontend Linting:   ${RED}FAILED${NC}"
        fi
    fi

    if [ "$FRONTEND_ONLY" = false ]; then
        if [ $TYPECHECK -eq 1 ]; then
            echo -e "  Type Checking:      ${GREEN}PASSED${NC}"
        else
            echo -e "  Type Checking:      ${RED}FAILED${NC}"
        fi
    fi
fi

if [ "$FRONTEND_ONLY" = false ]; then
    if [ $TEST_BACKEND -eq 1 ]; then
        echo -e "  Backend Tests:      ${GREEN}PASSED${NC}"
    else
        echo -e "  Backend Tests:      ${RED}FAILED${NC}"
    fi
fi

if [ "$BACKEND_ONLY" = false ]; then
    if [ $TEST_FRONTEND -eq 1 ]; then
        echo -e "  Frontend Tests:     ${GREEN}PASSED${NC}"
    else
        echo -e "  Frontend Tests:     ${RED}FAILED${NC}"
    fi
fi

echo ""

# Clean up test database
if [ "$FRONTEND_ONLY" = false ]; then
    rm -f backend/data/test_demographics.db
fi

if [ $TOTAL_FAILURES -eq 0 ]; then
    echo -e "${GREEN}=== ✅ All Tests Passed ===${NC}"
    echo ""
    echo "Coverage reports:"
    echo "  Backend:  backend/coverage_html/index.html"
    echo "  Frontend: frontend/coverage/index.html"
    exit 0
else
    echo -e "${RED}=== ❌ $TOTAL_FAILURES Stage(s) Failed ===${NC}"
    exit 1
fi
