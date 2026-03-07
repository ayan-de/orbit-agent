#!/bin/bash

################################################################################
# Orbit Agent - Production Install Script (with Prebuilt Release Support)
#
# Installs: Python Agent, Bridge, Frontend, Desktop TUI
# OS Support: Linux, macOS, WSL (Windows)
#
# Features:
# - Prebuilt releases for fast installation (~5 seconds)
# - Fallback to source installation if prebuilt unavailable
# - Automatic OS and platform detection
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

# Release configuration
RELEASE_VERSION="${RELEASE_VERSION:-latest}"
RELEASE_BASE_URL="${RELEASE_BASE_URL:-https://github.com/ayan-de/orbit-agent/releases}"
USE_PREBUILT="${USE_PREBUILT:-true}"

# Source installation configuration (fallback)
AGENT_REPO="https://github.com/ayan-de/orbit-agent.git"
CLAWDBOT_REPO="https://github.com/ayan-de/clawdbot.git"
INSTALL_DIR="$HOME/.orbit"
AGENT_DIR="$INSTALL_DIR/agent"
CLAWDBOT_DIR="$INSTALL_DIR/clawdbot"
LOG_DIR="$INSTALL_DIR/logs"
AGENT_PORT=8000
BRIDGE_PORT=3000
FRONTEND_PORT=5173

################################################################################
# OS Detection
################################################################################

detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [[ -f /proc/version ]] && grep -q "Microsoft" /proc/version; then
            echo "wsl"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

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
# Dependency Checks
################################################################################

check_dependencies() {
    log_info "Checking dependencies..."

    local missing_deps=()

    # Check curl (needed for prebuilt releases)
    if ! command -v curl &>/dev/null; then
        missing_deps+=("curl")
    fi

    # Check tar (needed for extraction)
    if ! command -v tar &>/dev/null; then
        missing_deps+=("tar")
    fi

    # Check sha256sum/shasum (for checksum verification)
    if ! command -v sha256sum &>/dev/null && ! command -v shasum &>/dev/null; then
        missing_deps+=("sha256sum or shasum")
    fi

    # Check git (needed for source installation)
    if ! command -v git &>/dev/null; then
        missing_deps+=("git")
    fi

    # Check Python 3.10+ (always needed)
    if ! command -v python3 &>/dev/null; then
        missing_deps+=("python3")
    elif ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else exit(1))" 2>/dev/null; then
        missing_deps+=("python3.10+")
    fi

    # Check Node.js (for bridge and frontend - always needed)
    if ! command -v node &>/dev/null; then
        missing_deps+=("nodejs")
    fi

    # Check npm (always needed)
    if ! command -v npm &>/dev/null; then
        missing_deps+=("npm")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        echo ""
        log_info "Please install missing dependencies:"
        if [[ "$OS_TYPE" == "macos" ]]; then
            echo "  brew install curl git python@3.11 node"
        elif [[ "$OS_TYPE" == "linux" ]]; then
            echo "  sudo apt install curl git python3.11 nodejs npm"
        elif [[ "$OS_TYPE" == "wsl" ]]; then
            echo "  sudo apt install curl git python3.11 nodejs npm"
        fi
        exit 1
    fi

    log_success "All dependencies installed"
}

################################################################################
# Directory Setup
################################################################################

setup_directories() {
    log_info "Setting up directories..."

    mkdir -p "$INSTALL_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$HOME/.orbit/memory"
    mkdir -p "$HOME/.orbit/logs/agent"
    mkdir -p "$HOME/.orbit/logs/bridge"
    mkdir -p "$HOME/.orbit/logs/frontend"

    log_success "Directories created"
}

################################################################################
# Prebuilt Release Installation
################################################################################

install_prebuilt_release() {
    log_info "Attempting prebuilt release installation..."

    local platform=$(detect_os)
    local arch=$(detect_arch)

    # Map platform names
    case "$platform" in
        wsl)
            platform="windows-wsl"
            ;;
    esac

    local release_name="orbit-agent-${RELEASE_VERSION}-${platform}-${arch}"
    local download_url="${RELEASE_BASE_URL}/download/${RELEASE_VERSION}/${release_name}.tar.gz"
    local checksum_url="${RELEASE_BASE_URL}/download/${RELEASE_VERSION}/${release_name}.tar.gz.sha256"
    local temp_dir="$HOME/.orbit_temp"

    log_info "Platform: $platform-$arch"
    log_info "Release: $release_name"

    # Create temp directory
    mkdir -p "$temp_dir"

    # Download release
    log_info "Downloading prebuilt release..."
    if ! curl -fsSL "$download_url" -o "$temp_dir/${release_name}.tar.gz"; then
        log_warn "Failed to download prebuilt release"
        return 1
    fi

    log_success "Download complete"

    # Download checksum
    log_info "Downloading checksum..."
    if ! curl -fsSL "$checksum_url" -o "$temp_dir/${release_name}.tar.gz.sha256"; then
        log_warn "Failed to download checksum"
        log_warn "Skipping verification (not recommended for production)"
    else
        # Verify checksum
        log_info "Verifying checksum..."
        if command -v sha256sum &>/dev/null; then
            cd "$temp_dir"
            if ! sha256sum -c "${release_name}.tar.gz.sha256"; then
                log_error "Checksum verification failed!"
                rm -f "$temp_dir/${release_name}.tar.gz"
                return 1
            fi
            cd - > /dev/null
        elif command -v shasum &>/dev/null; then
            cd "$temp_dir"
            if ! shasum -a 256 -c "${release_name}.tar.gz.sha256"; then
                log_error "Checksum verification failed!"
                rm -f "$temp_dir/${release_name}.tar.gz"
                return 1
            fi
            cd - > /dev/null
        fi
        log_success "Checksum verified"
    fi

    # Extract release
    log_info "Extracting release..."
    if ! tar -xzf "$temp_dir/${release_name}.tar.gz" -C "$temp_dir"; then
        log_error "Failed to extract release"
        return 1
    fi

    log_success "Extracted to $temp_dir"

    # Run the included installer
    log_info "Running included installer..."

    local extracted_dir="$temp_dir/orbit-agent-${RELEASE_VERSION}-${platform}-${arch}"
    if [ ! -d "$extracted_dir" ]; then
        # Try to find the extracted directory
        extracted_dir=$(find "$temp_dir" -maxdepth 1 -type d -name "orbit-agent-*" | head -1)
        if [ -z "$extracted_dir" ]; then
            log_error "Could not find extracted directory"
            return 1
        fi
    fi

    # Run the install script if it exists
    if [ -f "$extracted_dir/install.sh" ]; then
        cd "$extracted_dir"
        INSTALL_DIR="$INSTALL_DIR" ./install.sh
        cd - > /dev/null
        log_success "Prebuilt release installed"
    else
        # Manual installation
        log_info "Performing manual installation..."

        # Create agent directory
        mkdir -p "$AGENT_DIR"

        # Copy files
        cp -r "$extracted_dir"/* "$AGENT_DIR/"

        log_success "Prebuilt release installed manually"
    fi

    # Cleanup temp directory
    log_info "Cleaning up..."
    rm -rf "$temp_dir"

    log_success "Prebuilt release installation complete"
    return 0
}

################################################################################
# Clone Repositories (Fallback)
################################################################################

clone_repositories() {
    log_info "Cloning repositories..."

    # Clone Orbit Agent
    if [ ! -d "$AGENT_DIR" ]; then
        log_info "Cloning Orbit Agent..."
        git clone "$AGENT_REPO" "$AGENT_DIR"
        log_success "Orbit Agent cloned"
    else
        log_info "Orbit Agent already exists, updating..."
        cd "$AGENT_DIR"
        git pull
        log_success "Orbit Agent updated"
    fi

    # Clone Clawdbot (Bridge + Frontend + TUI)
    if [ ! -d "$CLAWDBOT_DIR" ]; then
        log_info "Cloning Clawdbot..."
        git clone "$CLAWDBOT_REPO" "$CLAWDBOT_DIR"
        log_success "Clawdbot cloned"
    else
        log_info "Clawdbot already exists, updating..."
        cd "$CLAWDBOT_DIR"
        git pull
        log_success "Clawdbot updated"
    fi
}

################################################################################
# Install Python Agent
################################################################################

install_agent() {
    log_info "Installing Python Agent..."

    cd "$AGENT_DIR"

    # Check if venv exists
    if [ ! -d ".venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv .venv
    fi

    # Activate venv and install dependencies
    source .venv/bin/activate

    log_info "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt

    log_success "Python Agent installed"
}

################################################################################
# Install Bridge and Frontend
################################################################################

install_clawdbot() {
    log_info "Installing Clawdbot (Bridge + Frontend)..."

    cd "$CLAWDBOT_DIR"

    # Check if pnpm is installed
    if ! command -v pnpm &>/dev/null; then
        log_info "Installing pnpm..."
        npm install -g pnpm
    fi

    # Install root dependencies
    log_info "Installing root dependencies..."
    pnpm install

    # Install bridge dependencies
    if [ -d "packages/bridge" ]; then
        log_info "Installing Bridge dependencies..."
        cd packages/bridge
        pnpm install
        cd ../..
    fi

    # Install frontend dependencies
    if [ -d "apps/web" ]; then
        log_info "Installing Frontend dependencies..."
        cd apps/web
        pnpm install
        cd ../..
    fi

    # Build frontend (SvelteKit)
    if [ -d "apps/web" ]; then
        log_info "Building Frontend..."
        cd apps/web
        pnpm build
        cd ../..
        log_success "Frontend built"
    fi

    log_success "Clawdbot installed"
}

################################################################################
# Environment Setup
################################################################################

setup_environment() {
    log_info "Setting up environment..."

    # Create .env file for agent
    if [ ! -f "$AGENT_DIR/.env" ]; then
        log_info "Creating .env file..."
        cat > "$AGENT_DIR/.env" << EOF
# Orbit Agent Configuration
PORT=$AGENT_PORT
DEBUG=true

# LLM Configuration
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
GOOGLE_API_KEY=your-google-key-here

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_BOT_WEBHOOK_URL=
TELEGRAM_POLLING_INTERVAL=5000

# Bridge Configuration
BRIDGE_URL=http://localhost:$BRIDGE_PORT
BRIDGE_API_KEY=
EOF
        log_warn "Please edit $AGENT_DIR/.env with your API keys and Telegram bot token"
    fi

    # Create .env file for clawdbot if needed
    if [ ! -f "$CLAWDBOT_DIR/.env" ]; then
        log_info "Creating clawdbot .env file..."
        cat > "$CLAWDBOT_DIR/.env" << EOF
# Clawdbot Configuration
BRIDGE_PORT=$BRIDGE_PORT
FRONTEND_PORT=$FRONTEND_PORT
AGENT_URL=http://localhost:$AGENT_PORT
EOF
        log_success "Clawdbot .env created"
    fi
}

################################################################################
# Systemd Service Setup (Linux/WSL only)
################################################################################

setup_services() {
    if [[ "$OS_TYPE" == "macos" ]]; then
        log_info "macOS detected - skipping systemd service setup"
        log_info "You'll need to manually start services or use launchd"
        return
    fi

    log_info "Setting up systemd services..."

    local user_services_dir="$HOME/.config/systemd/user"
    mkdir -p "$user_services_dir"

    # Orbit Agent Service
    cat > "$user_services_dir/orbit-agent.service" << EOF
[Unit]
Description=Orbit Agent
After=network.target

[Service]
Type=simple
WorkingDirectory=$AGENT_DIR
ExecStart=$AGENT_DIR/.venv/bin/python -m src.main
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

    # Bridge Service
    cat > "$user_services_dir/orbit-bridge.service" << EOF
[Unit]
Description=Orbit Bridge
After=network.target

[Service]
Type=simple
WorkingDirectory=$CLAWDBOT_DIR/packages/bridge
ExecStart=npm run start
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

    # Frontend Service
    cat > "$user_services_dir/orbit-frontend.service" << EOF
[Unit]
Description=Orbit Frontend
After=network.target

[Service]
Type=simple
WorkingDirectory=$CLAWDBOT_DIR/apps/web
ExecStart=npm run dev
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

    # Reload systemd
    systemctl --user daemon-reload
    systemctl --user enable orbit-agent.service
    systemctl --user enable orbit-bridge.service
    systemctl --user enable orbit-frontend.service

    log_success "Systemd services configured"
}

################################################################################
# Start Services
################################################################################

start_services() {
    log_info "Starting services..."

    if [[ "$OS_TYPE" == "linux" || "$OS_TYPE" == "wsl" ]]; then
        systemctl --user start orbit-agent.service
        systemctl --user start orbit-bridge.service
        systemctl --user start orbit-frontend.service
        log_success "Services started via systemd"
    elif [[ "$OS_TYPE" == "macos" ]]; then
        log_info "Starting services in background..."
        cd "$AGENT_DIR" && source .venv/bin/activate && nohup python -m src.main > "$LOG_DIR/agent.log" 2>&1 &
        cd "$CLAWDBOT_DIR/packages/bridge" && nohup npm run start > "$LOG_DIR/bridge.log" 2>&1 &
        cd "$CLAWDBOT_DIR/apps/web" && nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
        log_success "Services started in background"
    fi
}

################################################################################
# Display Summary
################################################################################

display_summary() {
    echo ""
    echo -e "${GREEN}═════════════════════════════════════════════${NC}"
    echo -e "${GREEN}          Orbit Agent - Installation Complete!         ${NC}"
    echo -e "${GREEN}═════════════════════════════════════════════${NC}"
    echo ""
    echo "Installation Location: $INSTALL_DIR"
    echo ""
    echo "Running Services:"
    echo "  • Python Agent:   http://localhost:$AGENT_PORT"
    echo "  • Bridge:         http://localhost:$BRIDGE_PORT"
    echo "  • Frontend:      http://localhost:$FRONTEND_PORT"
    echo ""
    echo "Web Interface:"
    echo "  • Open browser: http://localhost:$FRONTEND_PORT"
    echo ""
    echo "Telegram Integration:"
    echo "  1. Edit $AGENT_DIR/.env"
    echo "  2. Add your Telegram bot token: TELEGRAM_BOT_TOKEN=your-token"
    echo "  3. Add your API keys (OpenAI/Anthropic/Google)"
    echo "  4. Restart: systemctl --user restart orbit-agent"
    echo ""
    echo "Commands:"
    if [[ "$OS_TYPE" == "linux" || "$OS_TYPE" == "wsl" ]]; then
        echo "  • Start all:     systemctl --user start orbit-agent orbit-bridge orbit-frontend"
        echo "  • Stop all:      systemctl --user stop orbit-agent orbit-bridge orbit-frontend"
        echo "  • Restart all:  systemctl --user restart orbit-agent orbit-bridge orbit-frontend"
        echo "  • View logs:     journalctl --user -u orbit-agent -f"
    elif [[ "$OS_TYPE" == "macos" ]]; then
        echo "  • View logs:     tail -f $LOG_DIR/agent.log"
        echo "  • Stop services:  pkill -f 'python -m src.main'"
    fi
    echo ""
    echo "Documentation:"
    echo "  • Agent:         $AGENT_DIR/README.md"
    echo "  • Clawdbot:      $CLAWDBOT_DIR/README.md"
    echo ""
    log_warn "IMPORTANT: Configure your API keys in .env files before using!"
    echo ""
}

################################################################################
# Main Installation Flow
################################################################################

main() {
    clear
    echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║        Orbit Agent - Production Installer              ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}"
    echo ""

    # Detect OS
    OSTYPE=$(uname -s)
    OS_TYPE=$(detect_os)
    log_info "Detected OS: $OS_TYPE"
    echo ""

    # Install steps
    check_dependencies
    setup_directories

    # Try prebuilt installation first
    if [[ "$USE_PREBUILT" == "true" ]]; then
        log_info "Attempting prebuilt release installation..."
        if install_prebuilt_release; then
            log_success "Prebuilt release installed successfully!"
            log_info "Installation time: ~5 seconds"

            # Setup services
            setup_services

            # Ask to start services
            read -p "Start services now? (y/N): " -n 1 -r
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                start_services
            fi

            display_summary
            return 0
        else
            log_warn "Prebuilt release installation failed or unavailable"
            log_info "Falling back to source installation..."
        fi
    else
        log_info "Prebuilt installation disabled, using source installation"
    fi

    # Source installation (fallback)
    log_info "Starting source installation..."
    log_warn "This may take 2-5 minutes..."

    clone_repositories
    install_agent
    install_clawdbot
    setup_environment

    # OS-specific setup
    setup_services

    # Start services
    read -p "Start services now? (y/N): " -n 1 -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_services
    fi

    display_summary
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-prebuilt)
            USE_PREBUILT="false"
            shift
            ;;
        --version)
            RELEASE_VERSION="$2"
            shift 2
            ;;
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-prebuilt           Force source installation"
            echo "  --version VERSION       Use specific release version"
            echo "  --install-dir DIR       Installation directory (default: ~/.orbit)"
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
