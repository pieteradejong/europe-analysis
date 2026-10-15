#!/usr/bin/env bash
# init.sh — Python 3.12 virtualenv (venv/), pinned backend deps, caches cleared, frontend
# npm install and build. Reuses venv/ when it exists.
#   ./init.sh            set up, reusing venv/
#   ./init.sh --clean    rebuild venv/ from scratch
set -e
cd "$(dirname "$0")"
case "${1:-}" in -h|--help) sed -n '2,5p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;; esac
CLEAN=0
[ "${1:-}" = "--clean" ] && CLEAN=1

# Colors for output
green='\033[0;32m'
red='\033[0;31m'
reset='\033[0m'

# Function to check Python version
check_python_version() {
    local min_version="3.12.0"
    if ! command -v python3.12 &> /dev/null; then
        echo -e "${red}ERROR: Python 3.12 is not installed. Please install it first.${reset}"
        echo -e "You can install it using:"
        echo -e "  - macOS: brew install python@3.12"
        echo -e "  - Linux: Use your distribution's package manager"
        exit 1
    fi
    
    local current_version
    
    current_version=$(python3.12 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
    if [ "$(printf '%s\n' "$min_version" "$current_version" | sort -V | head -n1)" != "$min_version" ]; then
        echo -e "${red}ERROR: Python version 3.12 or higher is required. Current version: $current_version${reset}"
        exit 1
    fi
    echo -e "${green}Python version $current_version is compatible${reset}"
}

# Check Python version first
check_python_version

# --- Environment Variable Management ---
# Load .env file if present, but do not overwrite already-set environment variables
if [ -f ".env" ]; then
    # Only export variables that are not already set in the environment
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        if [[ -z "$key" || "$key" =~ ^# ]]; then
            continue
        fi
        # Only export if not already set
        if [ -z "${!key}" ]; then
            export "$key=$value"
        fi
    done < <(grep -v '^#' .env | grep -v '^$')
fi

# List of required environment variables (update as needed for your project)
required_vars=(
    # "EXAMPLE_API_KEY"
    # "EXAMPLE_API_SECRET"
    # Add more required variables here
)
missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done
if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${red}Error: Missing required environment variables:${reset}"
    for var in "${missing_vars[@]}"; do
        echo -e "  - $var"
    done
    echo -e "${red}Please export these variables in your shell or add them to your .env file and source it.${reset}"
    exit 1
fi
# --- End Environment Variable Management ---

# Reuse the virtual environment unless --clean asked for a rebuild
if [ "$CLEAN" = 1 ] && [ -d venv ]; then
    echo -e "${green}Removing existing Python virtual environment (venv/) (--clean) ...${reset}"
    rm -rf venv
fi
if [ -d venv ]; then
    echo -e "${green}Reusing existing Python virtual environment (venv/)${reset}"
else
    echo -e "${green}Creating Python 3.12 virtual environment (venv/) ...${reset}"
    python3.12 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Verify Python version in virtual environment
venv_python_version=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
if [[ ! "$venv_python_version" =~ ^3\.12\. ]]; then
    echo -e "${red}ERROR: Virtual environment Python version mismatch. Expected Python 3.12.x, got $venv_python_version${reset}"
    exit 1
fi
echo -e "${green}Using Python $venv_python_version in virtual environment${reset}"

# Remove Python caches
echo -e "${green}Removing all __pycache__, .pytest_cache, and .ruff_cache directories ...${reset}"
find . -type d -name "__pycache__" -exec rm -rf {} +
rm -rf .pytest_cache .ruff_cache

# Install Python dependencies
echo -e "${green}Installing Python dependencies ...${reset}"
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

# Initialize database and run migrations
echo -e "${green} Initializing database and running migrations ...${reset}"
mkdir -p backend/data
python -m alembic -c backend/alembic.ini upgrade head
echo -e "${green}Database migrations applied${reset}"

# Install pre-commit hooks
echo -e "${green}Installing pre-commit hooks ...${reset}"
pre-commit install

# Frontend setup: auto-create Vite React app if missing
if [ ! -d "frontend" ]; then
    echo -e "${green}Creating frontend/ with Vite + React ...${reset}"
    npm create vite@latest frontend -- --template react --force
fi

if [ -d "frontend" ]; then
    echo -e "${green}Cleaning frontend node_modules, dist, .vite, and caches ...${reset}"
    rm -rf frontend/node_modules frontend/dist frontend/.vite frontend/.cache frontend/.eslintcache

    echo -e "${green}Installing frontend dependencies ...${reset}"
    cd frontend
    npm install
    # Build or start frontend
    if grep -q '"build"' package.json; then
        echo -e "${green} Building frontend ...${reset}"
        npm run build
    elif grep -q '"dev"' package.json; then
        echo -e "${green}Starting frontend dev server ...${reset}"
        npm run dev &
    else
        echo -e "${red}No build or dev script found in frontend/package.json. Skipping frontend start.${reset}"
    fi
    cd ..
fi

echo
if [ -d "frontend" ]; then
    echo -e "${green}Initialization complete!${reset}"
    echo -e "${green}To activate the Python virtual environment: 'source venv/bin/activate'${reset}"
    echo -e "${green}To run the backend: './run.sh'${reset}"
    echo -e "${green}If the frontend dev server is running, visit: http://localhost:5173${reset}"
else
    echo -e "${green}Initialization complete!${reset}"
    echo -e "${green}To activate the Python virtual environment: 'source venv/bin/activate'${reset}"
    echo -e "${green}To run the backend: './run.sh'${reset}"
fi
