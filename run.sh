#!/bin/bash

# Exit on error
set -e

# Function to print section headers
print_section() {
    echo ""
    echo "=== $1 ==="
    echo ""
}

# Function to check if a service is running
check_service() {
    local url=$1
    local expected_status=$2
    local response=$(curl -s -w "\n%{http_code}" "$url")
    local body=$(echo "$response" | head -n1)
    local status_code=$(echo "$response" | tail -n1)
    
    if [ "$status_code" = "$expected_status" ]; then
        return 0
    fi
    return 1
}

# Function to wait for a service
wait_for_service() {
    local service=$1
    local url=$2
    local expected_status=${3:-200}  # Default to 200 if not provided
    local max_attempts=${4:-10}      # Default to 10 attempts if not provided
    local attempt=1

    echo "Waiting for $service to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if [ "$service" = "Frontend" ]; then
            # For frontend, we just check if the port is open
            if curl -s -f "http://localhost:5173" > /dev/null; then
                echo "✅ $service is ready!"
                return 0
            fi
        else
            # For backend, we check the health endpoint
            if check_service "$url" "$expected_status"; then
                echo "✅ $service is ready!"
                return 0
            fi
        fi
        
        echo "Attempt $attempt/$max_attempts: $service not ready yet..."
        if [ -f "backend/logs/backend.log" ]; then
            echo "Latest backend logs:"
            tail -n 5 backend/logs/backend.log
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    echo "❌ $service failed to start after $max_attempts attempts"
    if [ -f "backend/logs/backend.log" ]; then
        echo "Backend logs:"
        cat backend/logs/backend.log
    fi
    return 1
}

# Function to start a service in the background
start_service() {
    local name=$1
    local command=$2
    local log_file=$3

    echo "Starting $name..."
    # Ensure we're using the virtual environment's Python
    if [[ "$name" == "backend" ]]; then
        # Use the virtual environment's Python and uvicorn
        $command > "$log_file" 2>&1 &
    else
        $command > "$log_file" 2>&1 &
    fi
    echo $! > "${name}.pid"
    echo "✅ $name started (PID: $(cat ${name}.pid))"
}

# Function to stop a service
stop_service() {
    local name=$1
    if [ -f "${name}.pid" ]; then
        echo "Stopping $name..."
        kill $(cat "${name}.pid") 2>/dev/null || true
        rm "${name}.pid"
        echo "✅ $name stopped"
    fi
}

# Function to cleanup on exit
cleanup() {
    echo ""
    print_section "Cleaning Up"
    stop_service "backend"
    stop_service "frontend"
    exit 0
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

# Function to check Python version
check_python_version() {
    local required_version="3.12.0"
    local current_version=$(python3.12 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
    
    if [ "$(printf '%s\n' "$required_version" "$current_version" | sort -V | head -n1)" != "$required_version" ]; then
        echo "❌ Python version $required_version or higher is required. Current version: $current_version"
        exit 1
    fi
    echo "✅ Python version $current_version is compatible"
}

# Function to check required environment variables
check_env_vars() {
    local required_vars=()  # Empty by default - add variables as needed for your specific app
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        echo "❌ Missing required environment variables:"
        printf '%s\n' "${missing_vars[@]}"
        echo "Please set these variables in your .env file"
        exit 1
    fi
    echo "✅ All required environment variables are set"
}

# Function to check frontend dependencies
check_frontend_deps() {
    if [ ! -f "frontend/package.json" ]; then
        echo "❌ Frontend package.json not found"
        exit 1
    fi
    
    if [ ! -d "frontend/node_modules" ]; then
        echo "❌ Frontend node_modules not found. Please run 'npm install' in the frontend directory"
        exit 1
    fi
    echo "✅ Frontend dependencies are installed"
}

print_section "🚀 Starting Application"

# Check Python version
check_python_version

# Check environment variables
check_env_vars

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./init.sh first"
    exit 1
fi

# Function to verify Python environment
verify_python_env() {
    local python_path=$(which python3.12)
    if [[ ! "$python_path" =~ "venv" ]]; then
        echo "❌ Python3.12 is not running from virtual environment: $python_path"
        echo "Please ensure you're running the script from the project root directory"
        exit 1
    fi
    echo "✅ Using Python3.12 from virtual environment: $python_path"
}

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Verify Python environment
verify_python_env

# Verify uvicorn is installed in virtual environment
if ! python3.12 -c "import uvicorn" 2>/dev/null; then
    echo "❌ uvicorn is not installed in virtual environment"
    echo "Please run ./init.sh to install dependencies"
    exit 1
fi
echo "✅ uvicorn is installed in virtual environment"

# Create logs directory if it doesn't exist
mkdir -p backend/logs

# Start Backend
print_section "Starting Backend"
# Use the virtual environment's Python and uvicorn explicitly
start_service "backend" "python3.12 -m uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 --reload" "backend/logs/backend.log"

# Wait for backend to be ready
wait_for_service "Backend" "http://localhost:8000/health" "200" 10

# Check backend services
echo "Checking backend services..."
if ! check_service "http://localhost:8000/health/model" "200"; then
    echo "⚠️  Model service is not healthy"
fi

# Start Frontend
print_section "Starting Frontend"
check_frontend_deps
cd frontend
start_service "frontend" "npm run dev" "../backend/logs/frontend.log"
cd ..

# Wait for frontend to be ready (using port check instead of HTTP status)
wait_for_service "Frontend" "http://localhost:5173" "" 10

print_section "✅ All Services Running"
echo "The application is now available at:"
echo "   - Frontend: http://localhost:5173"
echo "   - Backend API: http://localhost:8000"
echo "   - API Documentation: http://localhost:8000/docs"
echo ""
echo "Health check endpoints:"
echo "   - Backend: http://localhost:8000/health"
echo "   - Model: http://localhost:8000/health/model"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep the script running and show logs
tail -f backend/logs/backend.log backend/logs/frontend.log 