# Orbit Agent - Installer Documentation

## Components

### 1. orbit-agent (Python)
**Repository:** https://github.com/ayan-de/orbit-agent

**What it does:**
- Main AI agent with LangGraph workflow
- Memory system (file-based)
- LLM integration (OpenAI, Anthropic, Google)
- Checkpointing for pause/resume
- Session management

**Installation:**
- Creates Python virtual environment
- Installs dependencies from requirements.txt
- Runs on port 8000 (configurable)

---

### 2. clawdbot (NestJS)
**Repository:** https://github.com/ayan-de/clawdbot

This repository contains THREE components in `apps/` directory:

#### 2a. Bridge (NestJS)
**Location:** `packages/bridge`

**What it does:**
- HTTP API server
- Receives commands from Orbit Agent
- Executes shell commands on user's PC
- Returns results to agent
- Runs on port 3000

**Why needed:**
- Separates agent logic from shell execution
- Provides safety verification layer
- Manages command execution permissions

#### 2b. Frontend (SvelteKit)
**Location:** `apps/web`

**What it does:**
- Web interface for Orbit Agent
- Chat UI for interacting with agent
- Settings panel for configuration
- Real-time WebSocket connection to agent

**Why needed:**
- User-friendly interface (alternative to Telegram)
- Visual feedback on agent status
- Easier configuration than editing .env files
- Runs on port 5173 (SvelteKit default)

#### 2c. Desktop TUI (Terminal UI)
**Location:** `apps/tui` (or similar)

**What it does:**
- Terminal-based user interface
- Runs directly in terminal
- No browser needed
- Lightweight, always available

**Why needed:**
- Quick terminal access
- Works without GUI
- For developers who prefer terminal

---

## Installation

### Quick Install (One Command)

```bash
curl -fsSL https://ayande.xyz/install.sh | bash
```

This:
1. Detects your OS (Linux/macOS/WSL)
2. Installs dependencies (git, python3, nodejs)
3. Clones both repositories to `~/.orbit/`
4. Sets up Python environment
5. Installs Node dependencies
6. Builds frontend
7. Creates systemd services (Linux/WSL)
8. Optionally starts services

---

### Manual Install (Advanced)

```bash
# Clone repositories
cd ~/
git clone https://github.com/ayan-de/orbit-agent.git .orbit/agent
git clone https://github.com/ayan-de/clawdbot.git .orbit/clawdbot

# Install Python Agent
cd ~/.orbit/agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install Clawdbot
cd ~/.orbit/clawdbot
npm install
cd apps/web && npm run build
cd ../packages/bridge && npm install
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 User's Local PC                   │
│                                                  │
│  ┌────────────┐    ┌──────────────────────┐   │
│  │ Frontend   │←──→│   Bridge (NestJS)   │   │
│  │ (apps/web) │    │   Port 3000          │   │
│  └────────────┘    └──────────┬───────────┘   │
│                            ↓                  │
│  ┌─────────────────────────┐   ↓               │
│  │  Agent (Python)      │←──┘               │
│  │  Port 8000            │                   │
│  │  Memory System       │                   │
│  └─────────────────────────┘                   │
└─────────────────────────────────────────────────────┘
              ↑           ↑
              │           │
      ┌─────┴──────────┴─────┐
      │  Telegram Bot (Polling)│ ← Runs on your server
      │  ayande.xyz            │
      └────────────────────────┘
```

**Communication flow:**
1. User sends message via Telegram → Telegram API
2. Your bot polls Telegram API → Gets message
3. Bot sends to local agent → HTTP request to localhost:8000
4. Agent processes message → Uses memory, LLM, tools
5. Agent needs to execute command → HTTP request to localhost:3000
6. Bridge executes on PC → Returns result
7. Agent sends response → Telegram Bot → User

---

## Accessing the Agent

### Via Web Interface
```
http://localhost:5173
```
- Modern web UI
- Chat interface
- Settings panel
- Memory visualization

### Via Telegram
```
@YourBotName

Message: "List files in /home/user"
```
- Messaging interface
- Works from anywhere
- Uses polling (works behind NAT)

### Via Terminal (if TUI available)
```bash
cd ~/.orbit/clawdbot/tui
npm run start
```
- Terminal-based UI
- No browser needed
- Keyboard-driven interaction

---

## Configuration

### Agent (.env)
Located at: `~/.orbit/agent/.env`

```bash
# LLM Configuration
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_POLLING_INTERVAL=5000  # milliseconds

# Bridge
BRIDGE_URL=http://localhost:3000
```

### Bridge (.env)
Located at: `~/.orbit/clawdbot/.env`

```bash
BRIDGE_PORT=3000
FRONTEND_PORT=5173
AGENT_URL=http://localhost:8000
```

---

## Service Management

### Linux/WSL (Systemd)

```bash
# Start all
systemctl --user start orbit-agent orbit-bridge orbit-frontend

# Stop all
systemctl --user stop orbit-agent orbit-bridge orbit-frontend

# Restart
systemctl --user restart orbit-agent

# View logs
journalctl --user -u orbit-agent -f
journalctl --user -u orbit-bridge -f
journalctl --user -u orbit-frontend -f
```

### macOS (Manual)

```bash
# Agent
cd ~/.orbit/agent && source .venv/bin/activate && python -m src.main

# Bridge
cd ~/.orbit/clawdbot/packages/bridge && npm run start

# Frontend
cd ~/.orbit/clawdbot/apps/web && npm run dev
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Python Module Not Found

```bash
cd ~/.orbit/agent
source .venv/bin/activate
pip install <module-name>
```

### Node Module Not Found

```bash
cd ~/.orbit/clawdbot
npm install
```

### View Logs

```bash
# Linux/WSL
tail -f ~/.orbit/logs/agent.log
tail -f ~/.orbit/logs/bridge.log
tail -f ~/.orbit/logs/frontend.log

# macOS
tail -f ~/Library/Logs/orbit/*.log
```

---

## Uninstallation

```bash
# Stop services (Linux/WSL)
systemctl --user stop orbit-agent orbit-bridge orbit-frontend

# Remove directories
rm -rf ~/.orbit

# Remove systemd services
rm ~/.config/systemd/user/orbit-*.service
systemctl --user daemon-reload
```

---

## Support

- **Documentation:** Check README.md in each repository
- **Issues:** Report on GitHub issues pages
- **Logs:** Check `~/.orbit/logs/` for detailed error messages
