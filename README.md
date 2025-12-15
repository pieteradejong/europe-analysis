# Python Base App

[![python-baseapp](https://github.com/pieteradejong/python-baseapp/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/pieteradejong/python-baseapp/actions/workflows/ci.yml)

A minimal, lean Python web application template that provides a clean starting point for new projects. Built with a focus on simplicity and maintainability, using only essential dependencies. The project emphasizes:

- 🎯 **Minimal Dependencies**: Only essential packages included
- 🚀 **Fast Development**: Quick setup and iteration
- 🔒 **Type Safety**: Built-in type checking without complexity
- 📦 **No External Services**: Runs without Redis, databases, or other external dependencies
- 🛠️ **Modern Tooling**: Latest stable versions of core tools
- 🧪 **Testing Ready**: Basic testing setup without over-engineering
- 🔐 **Security Headers**: Production-ready security features
- 📱 **Mobile Responsive**: Fully responsive frontend with mobile-first design

## Project Philosophy

This template is designed to be a minimal, practical starting point that you can build upon. It intentionally avoids:

- ❌ Complex dependency trees
- ❌ External service requirements
- ❌ Over-engineered solutions
- ❌ Unnecessary abstractions
- ❌ Development environment complexity

Instead, it focuses on:

- ✅ Essential dependencies only
- ✅ Fast local development
- ✅ Clear, maintainable code
- ✅ Practical best practices
- ✅ Easy onboarding for new developers
- ✅ Production-ready security
- ✅ Mobile-first responsive design

## Tech Stack

### Backend
- **Framework**: FastAPI 0.109.2 - Modern, fast web framework for building APIs with Python
- **Server**: Uvicorn 0.27.1 - Lightning-fast ASGI server
- **Data Validation**: Pydantic 2.6.1 - Data validation using Python type annotations
- **Configuration**: pydantic-settings - Type-safe configuration management
- **Environment**: Python 3.12.2 with strict type checking

### Development Tools
- **Code Quality**:
  - Black 24.2.0 - Code formatting
  - Ruff 0.2.2 - Fast Python linter (replaces multiple tools)
  - MyPy 1.8.0 - Static type checking
- **Testing**: pytest 8.3.5 - Testing framework with coverage support
- **Environment**: python-dotenv 1.0.1 - Environment variable management

### Frontend (Optional)
- **Framework**: React with Vite
- **Package Manager**: npm/yarn
- **Development**: Node.js 18+
- **Responsive Design**: Mobile-first CSS with modern breakpoints
- **Touch Optimization**: 44px minimum touch targets for accessibility
- **Performance**: Optimized for mobile networks and devices

## Features

- 🐍 Python 3.12.2 with strict type checking
- 🚀 FastAPI backend with automatic API documentation
  - OpenAPI/Swagger UI at `/docs`
  - ReDoc at `/redoc`
  - Automatic request validation
  - Async support
  - High performance
- 🔐 Security features built-in
  - Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
  - CORS configuration
  - Production-ready error handling
- ⚡ Modern frontend with Vite/React (optional)
- 📱 **Fully Mobile Responsive**
  - Mobile-first CSS design (320px to 1920px+)
  - Touch-friendly interactions with proper touch targets
  - Dynamic viewport height support for mobile browsers
  - Progressive enhancement across device sizes
  - Optimized for mobile networks and performance
  - Accessibility features (reduced motion, high contrast)
- 🔒 Type-safe configuration management with pydantic
- 📝 Comprehensive logging system
- 🧪 Testing setup with pytest and coverage
- 🎨 Code formatting with Black
- 🔍 Linting with Ruff
- 🔄 CI/CD ready

## Dependencies

We maintain a minimal set of dependencies to keep the project lean and maintainable:

### Core Dependencies (backend/requirements.txt)
```
fastapi==0.109.2    # Web framework
uvicorn==0.27.1     # ASGI server
pydantic==2.6.1     # Data validation
pydantic-settings==2.1.0 # Configuration
python-dotenv==1.0.1 # Environment variables
```

### Development Dependencies
```
black==24.2.0       # Code formatting
ruff==0.2.2         # Linting (replaces multiple tools)
mypy==1.8.0         # Type checking
pytest==8.3.5       # Testing
pytest-cov==6.0.0   # Test coverage
httpx==0.27.0       # HTTP client for testing
pre-commit==4.0.1   # Git hooks for code quality
```

Key points about our dependencies:
- Each package serves a specific, essential purpose
- No overlapping functionality
- Latest stable versions
- No external service requirements
- Minimal development setup

## Quick Start

### Prerequisites

- Python 3.12.2 (explicitly required)
  ```bash
  # macOS
  brew install python@3.12

  # Ubuntu/Debian
  sudo apt update
  sudo apt install python3.12 python3.12-venv

  # Verify installation
  python3.12 --version  # Should show Python 3.12.2
  ```
- Node.js 18+ (for frontend)
  ```bash
  # macOS
  brew install node@18

  # Ubuntu/Debian
  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
  sudo apt install nodejs

  # Verify installation
  node --version  # Should show v18.x.x
  ```
- Git
  ```bash
  # macOS
  brew install git

  # Ubuntu/Debian
  sudo apt install git
  ```

### Installation

1. Clone the repository:
   ```bash
   git clone <this-repository-url>
   cd python-baseapp
   ```

2. Make the initialization script executable:
   ```bash
   chmod +x init.sh
   ```

3. Run the initialization script:
   ```bash
   ./init.sh
   ```
   This will:
   - Verify Python 3.12.2 is installed
   - Create a virtual environment with Python 3.12.2
   - Install Python dependencies
   - **If no frontend/ exists, automatically create a new Vite + React app in frontend/**
   - **Fully reset the frontend: removes all caches, node_modules, dist, .vite, and other build artifacts**
   - Install frontend dependencies and build the frontend
   - Set up pre-commit hooks
   - Clean up any existing caches

   If you encounter any issues:
   - Ensure Python 3.12.2 is installed and available as `python3.12`
   - Check that the virtual environment is created with Python 3.12.2
   - Verify all dependencies are installed correctly

### Configuration

1. Create a `.env` file in the project root (or copy from `.env.example`):
   ```env
   APP_ENV=development
   APP_DEBUG=true
   APP_NAME="Python Base App"
   APP_VERSION="0.1.0"
   API_HOST=0.0.0.0
   API_PORT=8000
   LOG_LEVEL=INFO
   # LOG_FILE=backend/logs/app.log  # Uncomment to enable file logging
   # Add any required secrets or API keys here (never hardcode in code)
   ```

Alternatively, you can export variables in your shell before running `./init.sh`:
```bash
export APP_ENV=development
export APP_DEBUG=true
# ...
```

2. Create a `config.json` for application settings (optional):
   ```json
   {
       "CANDIDATE_ID": "your-id-here"
   }
   ```

### Running the Application

1. Start all services:
   ```bash
   ./run.sh
   ```
   This will:
   - Verify Python 3.12.2 is being used
   - Check required environment variables
   - Start the backend API (http://localhost:8000)
   - Start the frontend dev server (http://localhost:5173)
   - Start the API documentation (http://localhost:8000/docs)

2. View logs:
   ```bash
   tail -f backend/logs/backend.log backend/logs/frontend.log
   ```

3. Test the API endpoints:
   ```bash
   # App info
   curl http://localhost:8000/

   # Health checks
   curl http://localhost:8000/health
   curl http://localhost:8000/health/model

   # API documentation
   open http://localhost:8000/docs
   ```

### Troubleshooting

If you encounter issues:

1. **Python Version Issues**
   ```bash
   # Check Python version
   python3.12 --version  # Should show Python 3.12.2

   # If using a different version, install Python 3.12.2
   # macOS
   brew install python@3.12

   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3.12 python3.12-venv
   ```

2. **Virtual Environment Issues**
   ```bash
   # Remove existing virtual environment
   rm -rf venv

   # Recreate with correct Python version
   python3.12 -m venv venv
   source venv/bin/activate

   # Verify Python version in virtual environment
   python --version  # Should show Python 3.12.2
   ```

3. **Dependency Issues**
   ```bash
   # Ensure you're in the virtual environment
   source venv/bin/activate

   # Reinstall dependencies
   python -m pip install --upgrade pip
   python -m pip install -r backend/requirements.txt
   ```

## Mobile Responsiveness

This project implements a comprehensive mobile-first responsive design that ensures excellent user experience across all device sizes.

### Mobile-First Design Principles

The frontend follows modern mobile-first design principles:

1. **Progressive Enhancement**
   - Base styles work on 320px+ screens
   - Enhanced layouts for larger screens
   - Performance optimized for mobile networks

2. **Touch-First Interactions**
   - Minimum 44px touch targets for accessibility
   - Optimized tap highlights and touch actions
   - Mobile-friendly button and link sizing

3. **Responsive Breakpoints**
   ```css
   /* Mobile: 320px+ (base/default) */
   /* Tablet: 768px+ */
   /* Desktop: 1024px+ */
   /* Large Desktop: 1280px+ */
   /* Landscape Mobile: max-height 600px */
   ```

### Key Mobile Features

- **Flexible Layouts**: Components adapt from mobile stack to desktop grid
- **Dynamic Viewport**: Uses `100dvh` for proper mobile browser support
- **Touch Optimization**: Removes tap highlights, optimizes touch interactions
- **Network-Aware**: Optimized CSS and assets for mobile networks
- **Accessibility**: Supports reduced motion and high contrast preferences

### Responsive Components

1. **Logo Container**
   - Stacks vertically on mobile
   - Horizontal layout on tablet+
   - Progressive sizing (4em → 7em across breakpoints)

2. **Interactive Elements**
   - Full-width buttons on mobile with max-width constraints
   - Proper touch targets (44px minimum)
   - Hover states adapted for touch devices

3. **Typography**
   - Responsive font scaling using CSS custom properties
   - Optimized line heights for readability
   - Mobile-friendly text sizes

### Testing Mobile Responsiveness

#### Browser Development Tools
```bash
# Start the development server
./run.sh

# Test in browser dev tools:
# 1. Open http://localhost:5173
# 2. Open Chrome/Firefox dev tools (F12)
# 3. Toggle device simulation mode
# 4. Test various device sizes:
#    - iPhone SE (375px)
#    - iPhone 12 Pro (390px)
#    - iPad (768px)
#    - iPad Pro (1024px)
#    - Desktop (1280px+)
```

#### Real Device Testing
The Vite dev server is configured to allow network access for testing on real devices:

```bash
# Start the server
cd frontend && npm run dev

# Output shows network URLs:
# ➜  Local:   http://localhost:5173/
# ➜  Network: http://192.168.1.100:5173/  # Your local IP
# ➜  Network: http://10.0.0.50:5173/      # Additional network interfaces

# On your mobile device:
# 1. Connect to the same WiFi network
# 2. Open the Network URL in your mobile browser
# 3. Test touch interactions and responsiveness
```

#### Orientation Testing
Test both portrait and landscape orientations:
- **Portrait**: Standard mobile layout with vertical stacking
- **Landscape**: Optimized layout for landscape mobile devices
- **Tablet Rotation**: Smooth transitions between orientations

#### Performance Testing
Mobile performance considerations:
- **CSS Optimization**: Minified and optimized for mobile networks
- **Asset Loading**: Efficient chunking for faster initial loads
- **Touch Responsiveness**: Optimized for 60fps touch interactions
- **Network Aware**: Lightweight styles for slower connections

### Customizing Mobile Styles

The responsive design uses CSS custom properties for easy customization:

```css
/* In frontend/src/index.css */
:root {
  /* Typography Scale */
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  /* ... more sizes */

  /* Spacing Scale */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  /* ... more spacing */
}
```

To modify responsive behavior:
1. **Adjust Breakpoints**: Modify media query values in CSS files
2. **Customize Spacing**: Update CSS custom properties
3. **Touch Targets**: Modify minimum sizes for buttons and links
4. **Typography**: Adjust font scale for different screen sizes

### Accessibility Features

The mobile design includes comprehensive accessibility features:

- **Reduced Motion**: Respects user preferences for minimal animations
- **High Contrast**: Enhanced visibility in high contrast mode
- **Touch Targets**: Minimum 44px targets for easy interaction
- **Focus Indicators**: Clear focus states for keyboard navigation
- **Screen Reader**: Semantic HTML structure for assistive technologies

### Mobile Development Workflow

1. **Start with Mobile**: Design and test mobile-first
2. **Progressive Enhancement**: Add tablet and desktop features
3. **Real Device Testing**: Test on actual mobile devices regularly
4. **Performance Monitoring**: Keep mobile performance in mind
5. **Touch Testing**: Verify all interactions work well on touch screens

This mobile-first approach ensures that your application provides an excellent user experience across all devices while maintaining fast development velocity and code maintainability.

### Testing

This project follows a lean, practical testing approach focused on critical functionality and fast feedback:

#### Test Structure
```
backend/tests/
├── conftest.py           # Shared test fixtures
├── unit/                 # Unit tests
│   ├── test_config.py   # Configuration tests
│   ├── test_logging.py  # Logging tests
│   └── test_api.py      # API endpoint tests
└── integration/         # Integration tests
    └── test_app.py      # Application integration tests
```

#### Running Tests

1. **Run all tests**:
   ```bash
   source venv/bin/activate
   pytest backend/tests/
   ```

2. **Run with coverage**:
   ```bash
   source venv/bin/activate
   pytest backend/tests/ --cov=backend/src
   ```

3. **Run specific test categories**:
   ```bash
   # Run unit tests only
   pytest backend/tests/unit/

   # Run integration tests only
   pytest backend/tests/integration/

   # Run specific test file
   pytest backend/tests/unit/test_config.py
   ```

#### Test Categories

1. **Configuration Tests**
   - Environment variable loading
   - Configuration validation
   - Default values
   - JSON config loading

2. **Logging Tests**
   - Console logging setup
   - File logging setup
   - Log level configuration
   - Log format validation

3. **API Tests** (when endpoints are added)
   - Endpoint functionality
   - Request validation
   - Error handling
   - Response formats

4. **Integration Tests**
   - Application startup
   - Service initialization
   - Component interaction
   - Error recovery

#### Testing Philosophy

We focus on:
- ✅ Critical functionality
- ✅ Fast feedback
- ✅ Clear failure messages
- ✅ Minimal setup
- ✅ Practical coverage

We avoid:
- ❌ Testing implementation details
- ❌ Complex test setup
- ❌ Slow tests
- ❌ Test duplication
- ❌ Over-engineering

### Code Quality & Linting

This project enforces essential code quality standards with a focus on **development velocity** and fast feedback loops.

#### Quick Commands

```bash
# Check code quality (fast)
./lint.sh

# Auto-fix issues
./fix.sh

# Check with type checking (slower)
./lint.sh --with-types
```

#### Development Velocity Approach

**Fast Local Checks (< 2 seconds):**
- Ruff linting with auto-fix
- Black formatting
- Essential safety checks only

**Comprehensive Checks (on push):**
- MyPy type checking
- Bandit security scanning
- Full test suite

#### Linting Tools

1. **Ruff** - Fast Python linter and formatter
   - Replaces multiple tools (flake8, isort, pyupgrade, etc.)
   - Auto-fixes most issues
   - Extremely fast execution

2. **Black** - Code formatting
   - Consistent, opinionated formatting
   - Eliminates style debates
   - Integrates with all editors

3. **MyPy** - Type checking (on push only)
   - Strict type checking enabled
   - Catches type errors before runtime
   - Ensures type safety

#### Manual Linting Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Ruff linting
ruff check backend/                    # Check for issues
ruff check --fix backend/              # Auto-fix issues
ruff check --diff backend/             # Show what would be fixed

# Black formatting
black backend/                         # Format code
black --check backend/                 # Check formatting
black --diff backend/                  # Show formatting changes

# Type checking
mypy --strict --ignore-missing-imports --explicit-package-bases backend/src backend/tests
```

#### Pre-commit Hooks (Velocity Focused)

Pre-commit hooks run essential checks only for fast commits:

```bash
# Install pre-commit hooks (done automatically by init.sh)
source venv/bin/activate
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run black --all-files
```

#### Configured Checks

**Fast Local Checks (pre-commit):**
- Ruff linting with auto-fix
- Black formatting
- Essential safety checks (large files, merge conflicts, private keys)
- Python AST validation

**Comprehensive Checks (pre-push):**
- MyPy type checking
- Bandit security scanning

**Frontend Checks:**
- ESLint with lenient rules for development velocity
- No formatting enforcement (developer choice)

#### Configuration Files

- **pyproject.toml** - Main configuration for all tools
- **.pre-commit-config.yaml** - Minimal pre-commit hook configuration
- **lint.sh** - Local linting script
- **fix.sh** - Auto-fix script
- **frontend/eslint.config.js** - Lenient ESLint rules

#### Development Philosophy

**Development Velocity Priority:**
- Fast feedback loops (< 2 seconds for local checks)
- Auto-fix issues automatically where possible
- Heavy checks run on push, not commit
- Lenient rules that focus on real issues

**Practical Standards:**
- Focus on critical issues, not style preferences
- Allow developer flexibility where appropriate
- Balance code quality with development speed
- Consistent with modern development practices

**Developer Experience:**
- Works in all major editors
- Minimal friction in development workflow
- Clear, actionable error messages
- Easy to understand and modify

### Project Structure

```
python-baseapp/
├── LICENSE
├── README.md
├── activate.sh           # Virtual environment activation
├── init.sh              # Environment setup
├── run.sh               # Service management
├── lint.sh              # Code quality checking
├── fix.sh               # Auto-fix linting issues
├── venv/                # Python virtual environment (not tracked by git)
├── frontend/            # Frontend code (Vite React app)
│   ├── src/            # React components and logic
│   ├── public/         # Static assets
│   ├── vite.config.js  # Vite config
│   ├── package.json
│   ├── package-lock.json
│   └── ...
├── backend/             # Python backend code (FastAPI)
│   ├── src/
│   │   ├── main.py     # FastAPI app entrypoint
│   │   ├── __init__.py
│   │   └── library.py  # Shared backend logic
│   ├── requirements.txt # Python dependencies
│   ├── logs/           # Application logs
│   └── tests/          # Python tests
│       ├── conftest.py
│       ├── integration/
│       └── unit/
├── pyproject.toml       # Python project metadata & tool config
├── .pre-commit-config.yaml # Minimal pre-commit hook configuration
└── .env.example         # Environment variable template
```

## Best Practices

This project follows practical development standards that balance quality with velocity:

1. **Type Safety**
   - Strict type checking enabled (checked on push)
   - No untyped functions or variables
   - Comprehensive type hints
   - Type-safe configuration

2. **Configuration**
   - Environment variables for deployment
   - JSON config for application settings
   - Type-safe config validation
   - Environment-specific settings

3. **Logging**
   - Structured logging
   - Both console and file output
   - Configurable log levels
   - Proper error tracking

4. **Error Handling**
   - Custom exception classes
   - Proper error propagation
   - Contextual error messages
   - Comprehensive logging

5. **Security Best Practices**
   - Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
   - CORS configuration
   - Input validation at boundaries
   - Secure error handling (no information leakage)
   - Environment-aware security settings
   - No hardcoded secrets

6. **Development Velocity**
   - Fast local development with minimal friction
   - Quick feedback loops for essential checks
   - Heavy checks deferred to push time
   - Auto-fixing of common issues
   - Lenient rules focused on real problems
   - Clear separation of concerns
   - Practical best practices over rigid enforcement

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

[Your chosen license]

## Environment Variable Management

This project follows best practices for environment variable management:

- **Primary Source:** Environment variables set in the shell (e.g., via `export VAR=...` or in deployment environments) always take precedence.
- **Fallback:** If a variable is not set in the environment, it is loaded from a `.env` file (if present), but never overwrites already-set variables.
- **Validation:** All required environment variables are validated at startup by the `init.sh` script. If any are missing, a clear error is printed and initialization stops.
- **Security:** Secrets must never be hardcoded or checked into version control. Only use `.env` or shell exports for secrets.
- **Customization:** Update the `required_vars` list in `init.sh` to match your project's needs.

**Tip:** To set environment variables, either export them in your shell or add them to a `.env` file in the project root. The `.env` file is loaded automatically during initialization, but will not overwrite variables already set in your environment.
