#!/bin/bash

################################################################################
# Orbit Agent - Web Installer
# Hosted at: https://ayande.xyz/install.sh
# Usage: curl -fsSL https://ayande.xyz/install.sh | bash
################################################################################

set -euo pipefail  # Exit on error, pipe failures

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

################################################################################
# Web Installer URL (this file itself)
################################################################################

INSTALLER_URL="https://ayande.xyz/install.sh"
AGENT_REPO="https://github.com/ayan-de/orbit-agent.git"
CLAWDBOT_REPO="https://github.com/ayan-de/clawdbot.git"

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
# Logging
################################################################################

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

################################################################################
# Install Git (if not present)
################################################################################

ensure_git() {
    if ! command -v git &>/dev/null; then
        log_info "Git not found, installing..."

        if [[ "$OS_TYPE" == "macos" ]]; then
            if command -v brew &>/dev/null; then
                brew install git
            else
                log_error "Homebrew not found. Please install from https://brew.sh"
                exit 1
            fi
        elif [[ "$OS_TYPE" == "linux" || "$OS_TYPE" == "wsl" ]]; then
            sudo apt update
            sudo apt install -y git
        fi
    fi
}

################################################################################
# Install Python (if not present)
################################################################################

ensure_python() {
    if ! command -v python3 &>/dev/null; then
        log_info "Python 3 not found, installing..."

        if [[ "$OS_TYPE" == "macos" ]]; then
            brew install python@3.11
        elif [[ "$OS_TYPE" == "linux" || "$OS_TYPE" == "wsl" ]]; then
            sudo apt update
            sudo apt install -y python3.11 python3.11-venv
        fi
    fi

    # Check Python version
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else exit(1))" 2>/dev/null; then
        log_error "Python 3.10+ required. Please install Python 3.10 or later."
        exit 1
    fi
}

################################################################################
# Install Node.js (if not present)
################################################################################

ensure_nodejs() {
    if ! command -v node &>/dev/null; then
        log_info "Node.js not found, installing..."

        if [[ "$OS_TYPE" == "macos" ]]; then
            brew install node
        elif [[ "$OS_TYPE" == "linux" || "$OS_TYPE" == "wsl" ]]; then
            # Using NodeSource setup script
            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt install -y nodejs
        fi
    fi
}

################################################################################
# Clone Repositories
################################################################################

clone_repos() {
    INSTALL_DIR="$HOME/.orbit"
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"

    # Clone orbit-agent
    if [ ! -d "agent" ]; then
        log_info "Cloning Orbit Agent..."
        git clone "$AGENT_REPO" agent
    else
        log_info "Orbit Agent exists, updating..."
        cd agent && git pull && cd ..
    fi

    # Clone clawdbot
    if [ ! -d "clawdbot" ]; then
        log_info "Cloning Clawdbot..."
        git clone "$CLAWDBOT_REPO" clawdbot
    else
        log_info "Clawdbot exists, updating..."
        cd clawdbot && git pull && cd ..
    fi
}

################################################################################
# Run Main Install Script
################################################################################

run_install() {
    INSTALL_DIR="$HOME/.orbit"
    MAIN_SCRIPT="$INSTALL_DIR/agent/install.sh"

    # Clone repos first
    clone_repos

    # Run the main install script
    if [ -f "$MAIN_SCRIPT" ]; then
        log_info "Running main installation script..."
        bash "$MAIN_SCRIPT"
    else
        log_error "Main install script not found at $MAIN_SCRIPT"
        exit 1
    fi
}

################################################################################
# Main Function
################################################################################

main() {
    clear
    echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║        Orbit Agent - Web Installer                      ║${NC}"
    echo -e "${BLUE}║        Hosted: https://ayande.xyz               ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}"
    echo ""

    # Detect OS
    OSTYPE=$(uname -s)
    OS_TYPE=$(detect_os)
    log_info "Detected OS: $OS_TYPE"
    echo ""

    # Ensure dependencies
    ensure_git
    ensure_python
    ensure_nodejs

    log_success "All dependencies ready"

    echo ""
    # Run installation
    run_install

    echo ""
    log_success "Installation complete!"
}

# Run main
main
