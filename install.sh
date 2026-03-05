#!/bin/bash

################################################################################
# Orbit Agent - Production Install Script
#
# Installs: Python Agent, Bridge, Frontend, Desktop TUI
# OS Support: Linux, macOS, WSL (Windows)
################################################################################

set -euo pipefail  # Exit on error, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

################################################################################
# Configuration
################################################################################

AGENT_REPO="https://github.com/ayan-de/orbit-agent.git"
CLAWDBOT_REPO="https://github.com/ayan-de/clawdbot.git"
INSTALL_DIR="$HOME/.orbit"
AGENT_DIR="$INSTALL_DIR/agent"
CLAWDBOT_DIR="$INSTALL_DIR/clawdbot"
LOG_DIR="$INSTALL_DIR/logs"
AGENT_PORT=8000
BRIDGE_PORT=3000
FRONTEND_PORT=5173  # SvelteKit default

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

    # Check git
    if ! command -v git &>/dev/null; then
        missing_deps+=("git")
    fi

    # Check Python 3.10+
    if ! command -v python3 &>/dev/null; then
        missing_deps+=("python3")
    elif ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else exit(1))" 2>/dev/null; then
        missing_deps+=("python3.10+")
    fi

    # Check Node.js (for bridge and frontend)
    if ! command -v node &>/dev/null; then
        missing_deps+=("nodejs")
    fi

    # Check npm
    if ! command -v npm &>/dev/null; then
        missing_deps+=("npm")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        echo ""
        log_info "Please install missing dependencies:"
        if [[ "$OS_TYPE" == "macos" ]]; then
            echo "  brew install git python@3.11 node"
        elif [[ "$OS_TYPE" == "linux" ]]; then
            echo "  sudo apt install git python3.11 nodejs npm"
        elif [[ "$OS_TYPE" == "wsl" ]]; then
            echo "  sudo apt install git python3.11 nodejs npm"
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
# Clone Repositories
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

    # Install root dependencies
    log_info "Installing root dependencies..."
    npm install

    # Install bridge dependencies
    if [ -d "packages/bridge" ]; then
        log_info "Installing Bridge dependencies..."
        cd packages/bridge
        npm install
        cd ../..
    fi

    # Install frontend dependencies
    if [ -d "apps/web" ]; then
        log_info "Installing Frontend dependencies..."
        cd apps/web
        npm install
        cd ../..
    fi

    # Build frontend (SvelteKit)
    if [ -d "apps/web" ]; then
        log_info "Building Frontend..."
        cd apps/web
        npm run build
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
    echo -e "${BLUE}║           Orbit Agent - Production Installer              ║${NC}"
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

    # Display summary
    display_summary
}

# Run main function
main
