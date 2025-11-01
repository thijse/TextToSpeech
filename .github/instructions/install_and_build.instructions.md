---
applyTo: '/**'
---

# IGT Procedure Intelligence - Installation and Build Instructions

This document provides comprehensive guidance for setting up, building, and running the IGT Procedure Intelligence application. This system is built on the Tauri framework with a TypeScript/React frontend and Python backend for medical device integration.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Architecture](#project-architecture)
3. [Installation Process](#installation-process)
4. [Build Scripts Overview](#build-scripts-overview)
5. [Build Process Breakdown](#build-process-breakdown)
6. [Development Workflow](#development-workflow)
8. [Troubleshooting](#troubleshooting)
9. [Environment Configuration](#environment-configuration)

## Prerequisites

Before building the project, ensure you have the following installed:

### Required Tools

1. **Node.js and Yarn**
   - Node.js 18+ (recommended: latest LTS)
   - Yarn 4.x (specified in `package.json`: `yarn@4.9.1`)

2. **Python Environment**
   - Python 3.10+ 
   - UV package manager (for Python virtual environment management)

3. **Rust and Cargo**
   - Rust 1.70+ (latest stable recommended)
   - Cargo (comes with Rust)

4. **Tauri CLI**
   - Installed via yarn: `@tauri-apps/cli@^2.7.1`

### Network Requirements

- **Philips Network Access**: Required for Artifactory dependencies. If any access issues  occur ask the user if the VPN is connected
- **Internet Access**: For downloading packages from public registries

### Platform Support

- **Primary Platform**: Windows (PowerShell scripts provided)
- **Development Shell**: PowerShell (`pwsh.exe`)

## Project Architecture

The project follows a hybrid architecture:

```
igt-procedure-intelligence/
├── Frontend (TypeScript/React)    # Web UI components
│   ├── src/                      # React application source
│   ├── public/                   # Static assets
│   └── package.json              # Node.js dependencies
├── Backend (Rust + Python)       # Core application logic
│   ├── src-tauri/               # Tauri configuration and Rust code
│   │   ├── python/              # Python backend modules
│   │   ├── Cargo.toml           # Rust dependencies
│   │   └── pyproject.toml       # Python dependencies
└── Build Scripts                 # Automated build processes
    ├── full_build.bat           # Complete rebuild (only when builds keep breaking and for first-time setup)
    ├── build.bat                # Standard build (recommended)
    ├── run.bat                  # Quick run (assumes built)
    └── stop.bat                 # Stop running processes
```

### Technology Stack

- **Frontend**: React 19, TypeScript, Vite, Zustand (state management)
- **Backend**: Python 3.10+, Tauri 2.x, Rust
- **Build Tools**: Vite, Cargo, UV, Yarn
- **Async Runtime**: anyio (Python), Tokio (Rust)

## Installation Process

### Quick Start (Recommended)

For first-time setup or after pulling major changes:

```powershell
# Clone the repository (if not already done)
git clone <repository-url>
cd igt-procedure-intelligence

# Run complete build (handles all dependencies)
.\full_build.bat
```

### Manual Setup

If you prefer step-by-step installation:

1. **Install Frontend Dependencies**
   ```powershell
   yarn install
   ```

2. **Setup Python Environment**
   ```powershell
   cd src-tauri
   uv venv .venv --python-preference only-system
   .\.venv\Scripts\activate
   uv pip install -e ./
   cd ..
   ```

3. **Install Rust Dependencies**
   ```powershell
   cd src-tauri
   cargo install --path .
   cd ..
   ```

4. **Generate TypeScript Types**
   ```powershell
   yarn generate-types
   ```

## Build Scripts Overview

The project provides several build scripts for different use cases:

### `full_build.bat` - Complete Rebuild

**When to use**: First setup, or persistent build issues that require a clean slate. This takes longers, 
so only use when necessary.

**What it does**:
- Terminates any running cargo processes
- Checks Philips Artifactory connectivity
- Completely removes and recreates Python virtual environment
- Removes and rebuilds Rust target directory
- Installs all dependencies from scratch
- Launches development server

**Process flow**:
```batch
1. Process cleanup (kill cargo.exe)
2. Network connectivity check (Artifactory)
3. Clean Python environment (.venv removal/recreation)
4. Clean Rust build cache (target/ removal)
5. Python environment setup (uv venv + pip install)
6. Rust dependency installation (cargo install)
7. Frontend dependency installation (yarn)
8. Launch development server (yarn tauri dev)
```

### `build.bat` - Standard Build

**When to use**: Regular development, minor changes

**What it does**:
- Terminates running cargo processes
- Creates Python virtual environment (if missing)
- Activates Python environment
- Installs frontend dependencies
- Launches development server

**Process flow**:
```batch
1. Process cleanup (kill cargo.exe)
2. Python environment check/creation
3. Environment activation
4. Frontend dependencies (yarn)
5. Launch development server (yarn tauri dev)
```

### `run.bat` - Quick Run

**When to use**: When dependencies are already installed

**What it does**:
- Terminates running processes
- Activates existing Python environment
- Launches development server directly

### `stop.bat` - Stop Processes

**When to use**: To cleanly terminate running development servers

**What it does**:
- Terminates all cargo.exe processes and children

## Build Process Breakdown

### Phase 1: Environment Preparation

```powershell
# Process cleanup - ensures clean start
taskkill /F /FI "IMAGENAME eq cargo.exe" /T 2>nul
taskkill /F /IM cargo.exe 2>nul

# Network verification
ping -n 1 artifactory-ehv.ta.philips.com >nul 2>&1
```

**Why this matters**: Cargo processes can sometimes hang, blocking new builds. The Artifactory check ensures access to Philips-specific dependencies.

### Phase 2: Python Backend Setup

```powershell
cd src-tauri

# Virtual environment management
if exist .venv (
    rmdir /s /q .venv  # Full rebuild only
)
uv venv .venv --python-preference only-system

# Dependency installation
call .venv\Scripts\activate
uv pip install -e ./
```

**Key dependencies installed**:
- `pytauri`: Tauri-Python bridge
- `pydantic`: Data validation and serialization
- `anyio`: Structured concurrency
- `openai`: AI integration
- Medical device interfaces (CAN bus, space mouse, etc.)

### Phase 3: Rust Application Setup

```powershell
# Build cache cleanup (full rebuild only)
if exist target (
    rmdir /s /q target
)

# Rust dependency installation
cargo install --path .
```

**Key Rust components**:
- Tauri core and plugins
- System integration libraries
- Static/dynamic library generation

### Phase 4: Frontend Application Setup

```powershell
cd ..  # Back to root directory

# Node.js dependencies
yarn install

# TypeScript type generation from Python models
yarn generate-types
```

**Key frontend dependencies**:
- React 19 with TypeScript
- Tauri API bindings
- 3D rendering (Three.js)
- UI components and styling

### Phase 5: Development Server Launch

```powershell
# Start integrated development environment
yarn tauri dev
```

**What happens during `tauri dev`**:
1. Rust backend compilation
2. Python module loading and initialization
3. Frontend development server (Vite)
4. Hot-reload setup for both frontend and backend
5. Window management and system integration

## Development Workflow

### Recommended Development Cycle

1. **Initial Setup**
   ```powershell
   .\full_build.bat
   ```

2. **Daily Development**
   ```powershell
   .\build.bat        # Standard build
   # or
   .\run.bat          # If no dependency changes
   ```

3. **Clean Rebuild** (when facing issues)
   ```powershell
   .\stop.bat         # Stop current processes
   .\full_build.bat   # Complete rebuild
   ```

### Hot Reload Behavior

- **Frontend Changes**: Instant hot-reload via Vite
- **Python Backend Changes**: Automatic restart (may take 2-3 seconds)
- **Rust Changes**: Full recompilation (30-60 seconds)
- **Configuration Changes**: Usually requires full restart

### File Watching

The development server watches:
- `src/**` - Frontend React components
- `src-tauri/python/**` - Python backend modules
- `src-tauri/src/**` - Rust application code
- `src-tauri/tauri.conf.json` - Tauri configuration

## Production Build

### Creating Production Builds

```powershell
# Frontend production build
yarn build

# Full application bundle
yarn tauri build
```

### Build Outputs

Production builds generate:
- **Frontend**: Optimized static files in `dist/`
- **Application**: Platform-specific installer in `src-tauri/target/release/bundle/`


## Troubleshooting

### Debug Information

Enable verbose logging:
```powershell
# Environment variables for debugging
$env:RUST_LOG="debug"
$env:TAURI_DEBUG="true"
.\build.bat
```

### Log Locations

- **Tauri Logs**: Console output during development
- **Python Logs**: Check Python logging configuration in backend
- **Build Logs**: Terminal output during build process

## Environment Configuration

### Required Environment Variables

Some features require environment variables:

```powershell
# Azure OpenAI (for voice control)
$env:AZURE_OPENAI_API_KEY="your-api-key"
$env:AZURE_OPENAI_ENDPOINT="your-endpoint"

# Development settings
$env:RUST_LOG="info"  # Rust logging level
$env:PYTHONPATH="src-tauri/python"  # Python module path
```

### Configuration Files

Key configuration files:
- `src-tauri/tauri.conf.json` - Tauri application settings
- `src-tauri/pyproject.toml` - Python dependencies and metadata
- `src-tauri/Cargo.toml` - Rust dependencies and build settings
- `package.json` - Frontend dependencies and scripts
- `vite.config.ts` - Frontend build configuration


### Essential Commands

```powershell
# First-time setup or major rebuild
.\full_build.bat

# Regular development
.\build.bat

# Quick start (dependencies already installed)
.\run.bat

# Stop all processes
.\stop.bat

# Manual commands
yarn install                    # Frontend dependencies
yarn generate-types           # TypeScript type generation
yarn tauri dev                # Development server
yarn tauri build              # Production build
```

