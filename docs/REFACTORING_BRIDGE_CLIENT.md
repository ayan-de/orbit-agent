# Refactoring: Renamed `bridge/client.py` to `orchestrator_client.py`

> **Date**: 2026-02-28
> **Reason**: Clarifies that Python client calls NestJS Bridge orchestrator, not the full Bridge system.

---

## Changes Made

### 1. File Renamed
```
orbit-agent/src/bridge/client.py → orbit-agent/src/bridge/orchestrator_client.py
```

### 2. Imports Updated

**File**: `orbit-agent/src/tools/shell.py`
```python
# Before:
from src.bridge.client import bridge_client, BridgeCommandResponse

# After:
from src.bridge.orchestrator_client import orchestrator_client, BridgeCommandResponse
```

**File**: `orbit-agent/src/tools/file_ops.py`
```python
# Before:
from src.bridge.client import bridge_client, BridgeCommandResponse

# After:
from src.bridge.orchestrator_client import orchestrator_client, BridgeCommandResponse
```

### 3. Module Exports Updated

**File**: `orbit-agent/src/bridge/__init__.py`
```python
"""
Bridge client module for Orbit Agent.

Contains HTTP client for communicating with NestJS Bridge orchestrator.
"""

from .schemas import BridgeCommandRequest, BridgeCommandResponse
from .orchestrator_client import BridgeClient

__all__ = ['BridgeClient', 'BridgeCommandRequest', 'BridgeCommandResponse']
```

### 4. Usage Updated in Files

All references to `bridge_client` within `tools/file_ops.py` have been updated to `orchestrator_client`:
- Line 79: `await orchestrator_client.list_files(path=path)`
- Line 102: `await orchestrator_client.read_file(path=path)`
- Line 135: `await orchestrator_client.write_file(...)`
- Line 160: `await orchestrator_client.create_directory(...)`
- Line 189: `await orchestrator_client.delete_path(...)`

---

## Architectural Clarity

### Before Refactoring
```
Python Agent
└─ src.bridge.client
   └─ Calls NestJS Bridge (unclear scope)
   └─ Conflicts with TypeScript "bridge client" (DesktopClient)
```

### After Refactoring
```
Python Agent
└─ src.bridge.orchestrator_client (OrchestratorClient)
   └─ Calls NestJS Bridge Command Orchestrator
   └─ Clear: Python Agent → Orchestrator → Desktop TUI
   └─ No name conflict with TypeScript DesktopClient
```

---

## Import Pattern

When importing in Python tools:

```python
# Import both client and response types
from src.bridge.orchestrator_client import orchestrator_client, BridgeCommandResponse

# Or import from module
from src.bridge import BridgeClient
client = BridgeClient()
```

---

## Testing

To verify imports work:

```bash
cd orbit-agent
python -c "from src.bridge.orchestrator_client import orchestrator_client; print('Import successful')"
```

---

## Related Files

- `orbit-agent/src/bridge/orchestrator_client.py` - Renamed client
- `orbit-agent/src/bridge/schemas.py` - Request/response schemas (unchanged)
- `orbit-agent/src/tools/shell.py` - Shell tool (import updated)
- `orbit-agent/src/tools/file_ops.py` - File operations tools (import updated)
- `orbit-agent/src/bridge/__init__.py` - Module exports (updated)

---

## Next Steps

This resolves Point #2 from the TypeScript/Python ambiguity analysis. Remaining points to address:

1. **Point #3**: Rename TypeScript `DesktopClient` or clarify both client purposes
2. **Point #5**: Consolidate memory to single system (choose: TypeScript PostgreSQL OR Python Markdown)
3. **Point #6**: Define clear tool boundary between Python tool definitions and TypeScript execution

---

## API Reference

### BridgeClient (OrchestratorClient)

```python
class BridgeClient:
    """Client for communicating with NestJS Bridge Command Orchestrator."""

    def __init__(
        self,
        base_url: str = settings.BRIDGE_URL,
        api_key: str = settings.BRIDGE_API_KEY,
    )

    async def execute_command(
        self, cmd: str, args: list = None, cwd: str = None, trusted: bool = False
    ) -> BridgeCommandResponse

    async def list_files(self, path: str = ".") -> BridgeCommandResponse

    async def read_file(self, path: str) -> BridgeCommandResponse

    async def write_file(
        self, path: str, content: str, mode: str = "write", create_dirs: bool = False
    ) -> BridgeCommandResponse

    async def create_directory(
        self, path: str, create_parents: bool = True, mode: str = "0755"
    ) -> BridgeCommandResponse

    async def delete_path(
        self, path: str, recursive: bool = False, force: bool = False
    ) -> BridgeCommandResponse

    async def get_file_info(self, path: str) -> BridgeCommandResponse
```

### BridgeCommandResponse

```python
class BridgeCommandResponse(BaseModel):
    """Response from command execution via Bridge Orchestrator."""

    exit_code: int
    stdout: Optional[str]
    stderr: Optional[str]
    error: Optional[str]
    success: bool
```

---

> **Status**: Complete
> **Impact**: Resolves naming confusion, clarifies architecture boundaries
