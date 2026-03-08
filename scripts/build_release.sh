#!/bin/bash

################################################################################
# Orbit Agent - Prebuilt Release Build Script
#
# Creates platform-specific prebuilt releases for Orbit Agent
# Supports: Linux, macOS, Windows (WSL)
################################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

################################################################################
# Configuration
################################################################################

VERSION="${VERSION:-latest}"
OUTPUT_DIR="${OUTPUT_DIR:-./releases}"
# Convert OUTPUT_DIR to absolute path immediately
mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"

ORBIT_AGENT_DIR="${ORBIT_AGENT_DIR:-.}"
ORBIT_AGENT_DIR="$(cd "$ORBIT_AGENT_DIR" && pwd)"

CLAWDBOT_DIR="${CLAWDBOT_DIR:-../clawdbotClone}"

# Detect platform
detect_platform() {
    case "$(uname -s)" in
        Linux*)
            if grep -q "Microsoft" /proc/version 2>/dev/null; then
                echo "windows-wsl"
            else
                echo "linux"
            fi
            ;;
        Darwin*)
            echo "macos"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            echo "windows"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

PLATFORM=$(detect_platform)

# Architecture detection
detect_arch() {
    case "$(uname -m)" in
        x86_64|amd64)
            echo "x64"
            ;;
        aarch64|arm64)
            echo "arm64"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

ARCH=$(detect_arch)

################################################################################
# Logging Functions
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

################################################################################
# Directory Setup
################################################################################

setup_build_dirs() {
    log_info "Setting up build directories..."

    mkdir -p "$OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR/temp"

    log_success "Build directories created"
}

################################################################################
# Build Python Agent
################################################################################

build_python_agent() {
    local target_dir="$1"

    log_info "Packaging Python Agent..."

    # Copy source code
    log_info "Copying Python source code..."
    cp -r "$ORBIT_AGENT_DIR/src" "$target_dir/"

    # Copy configuration files
    log_info "Copying configuration files..."
    if [ -f "$ORBIT_AGENT_DIR/.env.example" ]; then
        cp "$ORBIT_AGENT_DIR/.env.example" "$target_dir/.env.example"
    fi
    if [ -f "$ORBIT_AGENT_DIR/requirements.txt" ]; then
        cp "$ORBIT_AGENT_DIR/requirements.txt" "$target_dir/"
    fi
    if [ -f "$ORBIT_AGENT_DIR/pyproject.toml" ]; then
        cp "$ORBIT_AGENT_DIR/pyproject.toml" "$target_dir/"
    fi
    if [ -f "$ORBIT_AGENT_DIR/alembic.ini" ]; then
        cp "$ORBIT_AGENT_DIR/alembic.ini" "$target_dir/"
    fi

    # Copy migrations if they exist
    if [ -d "$ORBIT_AGENT_DIR/migrations" ]; then
        cp -r "$ORBIT_AGENT_DIR/migrations" "$target_dir/"
    fi

    # Copy documentation
    if [ -f "$ORBIT_AGENT_DIR/README.md" ]; then
        cp "$ORBIT_AGENT_DIR/README.md" "$target_dir/"
    fi
    if [ -f "$ORBIT_AGENT_DIR/CLAUDE.md" ]; then
        cp "$ORBIT_AGENT_DIR/CLAUDE.md" "$target_dir/"
    fi

    # Create start script that handles venv creation
    cat > "$target_dir/start_agent.sh" << 'EOF'
#!/bin/bash
# Find the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for Python virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Set PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# Start the agent
python -m src.main
EOF

    chmod +x "$target_dir/start_agent.sh"

    log_success "Python Agent packaged successfully"
}

################################################################################
# Build Node.js Components
################################################################################

build_nodejs_components() {
    local target_dir="$1"

    if [ ! -d "$CLAWDBOT_DIR" ]; then
        log_warn "ClawdbotClone directory not found at $CLAWDBOT_DIR"
        log_warn "Skipping Node.js components build"
        return
    fi

    log_info "Building Node.js components..."

    # Check if pnpm is installed
    if ! command -v pnpm &>/dev/null; then
        log_warn "pnpm not found. Installing pnpm..."
        npm install -g pnpm
    fi

    # Copy clawdbotClone source
    log_info "Copying ClawdbotClone source code..."
    cp -r "$CLAWDBOT_DIR" "$target_dir/clawdbot"

    # Install dependencies
    log_info "Installing Node.js dependencies..."
    cd "$target_dir/clawdbot"
    pnpm install --frozen-lockfile

    # Build all packages using Turbo (handles dependencies automatically)
    log_info "Building all packages (Common, Adapters, Desktop, Bridge, Web)..."
    pnpm build

    log_success "Turbo build completed successfully"

    # Verify builds
    log_info "Verifying package builds..."

    # Check Common package
    if [ -f "packages/common/dist/index.js" ]; then
        log_success "Common package built"
    else
        log_warn "Common package build not found"
    fi

    # Check Desktop TUI
    if [ -f "packages/desktop/dist/index.js" ]; then
        log_success "Desktop TUI built"
    else
        log_warn "Desktop TUI build not found"
    fi

    # Check NestJS Bridge
    if [ -f "packages/bridge/dist/main.js" ]; then
        log_success "NestJS Bridge built"
    else
        log_warn "NestJS Bridge build not found"
    fi

    # Web Dashboard is hosted at ayande.xyz, skipping local build
    log_info "Skipping Web Dashboard build (hosted at ayande.xyz)"

    # Organize release structure - remove development files
    log_info "Organizing release structure..."

    # Remove development artifacts
    rm -rf .git
    rm -rf .claude
    rm -rf .pytest_cache
    rm -rf .turbo

    # Remove source directories (keeping dist builds)
    find packages -name "src" -type d -exec rm -rf {} + 2>/dev/null || true
    find apps -name "src" -type d -exec rm -rf {} + 2>/dev/null || true

    # Remove dev dependencies to reduce size
    log_info "Removing development dependencies..."
    pnpm prune --prod

    # Remove test directories
    find packages -name "__tests__" -type d -exec rm -rf {} + 2>/dev/null || true
    find packages -name "test" -type d -exec rm -rf {} + 2>/dev/null || true
    find apps -name "__tests__" -type d -exec rm -rf {} + 2>/dev/null || true
    find apps -name "test" -type d -exec rm -rf {} + 2>/dev/null || true

    # Create start scripts for Node.js components
    log_info "Creating start scripts..."

    # NestJS Bridge start script
    cat > "$target_dir/start_bridge.sh" << 'EOF'
#!/bin/bash
# Find the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start NestJS Bridge
cd "$SCRIPT_DIR/clawdbot/packages/bridge"
node dist/main.js
EOF
    chmod +x "$target_dir/start_bridge.sh"

    # Desktop TUI start script
    cat > "$target_dir/start_desktop.sh" << 'EOF'
#!/bin/bash
# Find the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start Desktop TUI
cd "$SCRIPT_DIR/clawdbot/packages/desktop"
node dist/index.js
EOF
    chmod +x "$target_dir/start_desktop.sh"

    # Web Dashboard start script (Optional, usually hosted)
    cat > "$target_dir/start_web.sh" << 'EOF'
#!/bin/bash
# Find the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Open the hosted web dashboard
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "https://ayande.xyz"
else
    xdg-open "https://ayande.xyz" || echo "Please visit https://ayande.xyz in your browser"
fi
EOF
    chmod +x "$target_dir/start_web.sh"

    # Dev mode start script (for development)
    cat > "$target_dir/start_dev.sh" << 'EOF'
#!/bin/bash
# Find the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start all services in dev mode
cd "$SCRIPT_DIR/clawdbot"
pnpm dev
EOF
    chmod +x "$target_dir/start_dev.sh"

    log_success "Node.js components built successfully"
}

################################################################################
# Create Installer Scripts
################################################################################

create_installer_scripts() {
    local target_dir="$1"

    log_info "Creating installer scripts..."

    # Create main install script
    cat > "$target_dir/install.sh" << 'INSTALL_SCRIPT'
#!/bin/bash

################################################################################
# Orbit Agent - Quick Installer for Prebuilt Release
#
# This script sets up the prebuilt Orbit Agent installation
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.orbit}"
ORBIT_DIR="$INSTALL_DIR/agent"

log_info "Orbit Agent - Prebuilt Release Installer"
log_info "Installing from: $SCRIPT_DIR"
log_info "Installing to: $INSTALL_DIR"

# Create directories
log_info "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/memory"

# Copy files
log_info "Copying files..."
if [ "$SCRIPT_DIR" != "$ORBIT_DIR" ]; then
    cp -r "$SCRIPT_DIR"/* "$ORBIT_DIR/"
else
    log_info "Already in target directory, skipping copy"
fi

# Setup configuration
log_info "Setting up configuration..."
if [ ! -f "$ORBIT_DIR/.env" ]; then
    if [ -f "$ORBIT_DIR/.env.example" ]; then
        cp "$ORBIT_DIR/.env.example" "$ORBIT_DIR/.env"
        log_warn "Please edit $ORBIT_DIR/.env with your API keys"
    fi
fi

# Setup PM2 (Node.js Process Manager)
log_info "Setting up PM2 process manager..."
if ! command -v pm2 &>/dev/null; then
    log_info "Installing PM2 via npm..."
    npm install -g pm2 || sudo npm install -g pm2 || true
fi

if command -v pm2 &>/dev/null; then
    # Create ecosystem file
    cat > "$ORBIT_DIR/ecosystem.config.js" << EOF
module.exports = {
  apps: [
    {
      name: "orbit-agent",
      script: "$ORBIT_DIR/start_agent.sh",
      cwd: "$ORBIT_DIR",
      autorestart: true,
      env: {
        NODE_ENV: "production"
      }
    },
    {
      name: "orbit-bridge",
      script: "$ORBIT_DIR/clawdbot/packages/bridge/dist/main.js",
      cwd: "$ORBIT_DIR/clawdbot/packages/bridge",
      autorestart: true,
      env: {
        NODE_ENV: "production",
        PORT: 8443
      }
    }
  ]
};
EOF

    # Start services
    log_info "Starting core services with PM2..."
    pm2 start "$ORBIT_DIR/ecosystem.config.js"
    pm2 save || true
    log_success "Services started in background via PM2"
else
    log_warn "PM2 not found. Services must be started manually."
fi

log_success "Installation complete!"
echo ""
echo -e "${YELLOW}To start the Desktop TUI, you need to authorize it:${NC}"
echo "1. Go to https://ayande.xyz/settings/desktop"
echo "2. Authorize and copy your Orbit Token"
echo ""
read -p "Paste your Orbit Token: " orbit_token

if [ -n "$orbit_token" ]; then
    log_info "Starting Desktop TUI..."
    cd "$ORBIT_DIR" && ./start_desktop.sh --token "$orbit_token"
else
    log_warn "No token provided. Start manually with: ./start_desktop.sh --token <TOKEN>"
fi
INSTALL_SCRIPT

    chmod +x "$target_dir/install.sh"

    # Create uninstall script
    cat > "$target_dir/uninstall.sh" << 'UNINSTALL_SCRIPT'
#!/bin/bash

################################################################################
# Orbit Agent - Uninstaller
################################################################################

set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-$HOME/.orbit}"

log_info "Uninstalling Orbit Agent from $INSTALL_DIR..."

# Stop services
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    systemctl --user stop orbit-agent orbit-bridge 2>/dev/null || true
    systemctl --user disable orbit-agent orbit-bridge 2>/dev/null || true
    rm -f "$HOME/.config/systemd/user/orbit-agent.service"
    rm -f "$HOME/.config/systemd/user/orbit-bridge.service"
    systemctl --user daemon-reload 2>/dev/null || true
fi

# Remove files
read -p "Remove installation directory $INSTALL_DIR? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$INSTALL_DIR"
    log_success "Installation directory removed"
else
    log_info "Keeping installation directory"
fi

log_success "Uninstall complete!"
UNINSTALL_SCRIPT

    chmod +x "$target_dir/uninstall.sh"

    log_success "Installer scripts created"
}

################################################################################
# Create Release Archive
################################################################################

create_release_archive() {
    local platform="$1"
    local arch="$2"
    local source_dir="$3"
    local release_name="orbit-agent-${VERSION}-${platform}-${arch}"
    local archive_name="${release_name}.tar.gz"

    log_info "Creating release archive: $archive_name"

    # Create archive
    # Use -C logically to avoid path issues
    cd "$source_dir/.."
    tar -czf "$OUTPUT_DIR/$archive_name" "$(basename "$source_dir")"

    # Generate checksum
    log_info "Generating checksum..."
    if command -v sha256sum &>/dev/null; then
        sha256sum "$OUTPUT_DIR/$archive_name" > "$OUTPUT_DIR/${archive_name}.sha256"
    elif command -v shasum &>/dev/null; then
        shasum -a 256 "$OUTPUT_DIR/$archive_name" > "$OUTPUT_DIR/${archive_name}.sha256"
    fi

    # Get file size
    local file_size=$(du -h "$OUTPUT_DIR/$archive_name" | cut -f1)

    log_success "Release archive created: $archive_name ($file_size)"
    log_info "Checksum: $OUTPUT_DIR/${archive_name}.sha256"
}

################################################################################
# Cleanup
################################################################################

cleanup() {
    log_info "Cleaning up temporary files..."
    rm -rf "$OUTPUT_DIR/temp"
    log_success "Cleanup complete"
}

################################################################################
# Main Build Process
################################################################################

main() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     Orbit Agent - Prebuilt Release Builder        ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}"
    echo ""
    log_info "Version: $VERSION"
    log_info "Platform: $PLATFORM"
    log_info "Architecture: $ARCH"
    echo ""

    # Setup
    setup_build_dirs

    # Create temporary build directory
    BUILD_DIR="$OUTPUT_DIR/temp/orbit-agent-${VERSION}-${PLATFORM}-${ARCH}"
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"

    # Build components
    build_python_agent "$BUILD_DIR"
    # build_nodejs_components "$BUILD_DIR" # Decoupled! handled by clawdbotClone repo
    create_installer_scripts "$BUILD_DIR"

    # Create release archive
    create_release_archive "$PLATFORM" "$ARCH" "$BUILD_DIR"

    # Cleanup
    cleanup

    echo ""
    echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}              Build Complete!                           ${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
    echo ""
    log_info "Release artifacts: $OUTPUT_DIR"
    log_info "Archive: $OUTPUT_DIR/orbit-agent-${VERSION}-${PLATFORM}-${ARCH}.tar.gz"
    log_info "Checksum: $OUTPUT_DIR/orbit-agent-${VERSION}-${PLATFORM}-${ARCH}.tar.gz.sha256"
    echo ""
    log_info "To install: tar -xzf orbit-agent-${VERSION}-${PLATFORM}-${ARCH}.tar.gz"
    log_info "           cd orbit-agent-${VERSION}-${PLATFORM}-${ARCH}"
    log_info "           ./install.sh"
    echo ""
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --arch)
            ARCH="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --orbit-agent-dir)
            ORBIT_AGENT_DIR="$2"
            shift 2
            ;;
        --clawdbot-dir)
            CLAWDBOT_DIR="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --version VERSION       Set release version (default: latest)"
            echo "  --platform PLATFORM     Force platform (linux/macos/windows-wsl/windows)"
            echo "  --arch ARCH             Force architecture (x64/arm64)"
            echo "  --output DIR            Output directory (default: ./releases)"
            echo "  --orbit-agent-dir DIR   Orbit agent source directory"
            echo "  --clawdbot-dir DIR      ClawdbotClone source directory"
            echo "  --help, -h              Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main
main
