# Tool Danger Levels Reference

This document catalogs all Orbit Agent tools with their assigned danger levels and the rationale for each classification.

## Danger Level Scale

| Range | Category | Description | Confirmation Required |
|-------|-----------|-------------|---------------------|
| 0-2 | **SAFE** | Read-only or harmless operations | No |
| 3-5 | **MODERATE** | Write operations or external actions | Recommended |
| 6-10 | **DANGEROUS** | Destructive or irreversible operations | Yes |

## Tool Catalog

### Safe Tools (0-2) - No confirmation required

| Tool | Danger Level | Category | Description |
|------|--------------|-----------|-------------|
| `list_files` | 1 | SYSTEM | List files and directories. Purely read-only operation. |
| `read_file` | 1 | SYSTEM | Read contents of a file. Purely read-only operation. |

### Moderate Tools (3-5) - Confirmation recommended

| Tool | Danger Level | Category | Description |
|------|--------------|-----------|-------------|
| `create_directory` | 2 | SYSTEM | Create a new directory. Safe but creates file system structure. |
| `write_file` | 3 | SYSTEM | Write content to a file. Can modify existing files. |
| `gmail_send` | 3 | INTEGRATION | Send email via Gmail. External action with rate limiting. |
| `shell_exec` | 5 | SYSTEM | Execute shell commands. Can be dangerous depending on command. |

### Dangerous Tools (6-10) - Confirmation required

| Tool | Danger Level | Category | Description |
|------|--------------|-----------|-------------|
| `delete_path` | 4 | SYSTEM | Delete files or directories. Destructive operation. |

## Danger Level Assignments

### Shell Tool (`shell_exec`)
- **Danger Level: 5**
- **Requires Confirmation: Yes**
- **Rationale:** Shell commands can execute arbitrary operations, including file deletion, system configuration changes, etc. While commands go through safety checks, the potential for damage is high.

### File Operation Tools

#### `list_files`
- **Danger Level: 1**
- **Requires Confirmation: No**
- **Rationale:** Purely read-only. No risk of data loss or system changes.

#### `read_file`
- **Danger Level: 1**
- **Requires Confirmation: No**
- **Rationale:** Purely read-only. No risk of data loss or system changes.

#### `write_file`
- **Danger Level: 3**
- **Requires Confirmation: Yes**
- **Rationale:** Can overwrite existing files. Moderate risk of data corruption or accidental modification.

#### `create_directory`
- **Danger Level: 2**
- **Requires Confirmation: Yes**
- **Rationale:** Creates file system structure but doesn't modify existing data. Low to moderate risk.

#### `delete_path`
- **Danger Level: 4**
- **Requires Confirmation: Yes**
- **Rationale:** Destructive operation that permanently removes data. High risk of data loss.

### Integration Tools

#### `gmail_send`
- **Danger Level: 3**
- **Requires Confirmation: Yes**
- **Rationale:** External action that sends email to recipients. Rate limited to prevent abuse, but still requires confirmation.

## Setting Danger Levels for New Tools

When creating new tools, follow these guidelines:

1. **Read-only operations**: Use danger level 0-2
   - Querying APIs, reading files, listing resources

2. **Write operations**: Use danger level 3-5
   - Creating files, updating databases, sending messages

3. **Destructive operations**: Use danger level 6-10
   - Deleting files, dropping databases, pushing to production

4. **External integrations**: Use danger level 3-10 depending on impact
   - Low-impact (email, Slack): 3-5
   - High-impact (deployments, database changes): 6-10

## Confirmation Logic

Tools require user confirmation when:

1. **Explicitly set**: `requires_confirmation = True`
2. **Danger level threshold**: `danger_level > user_permission_level`
3. **Safe override**: User can approve dangerous operations for one-time execution

The default user permission level is 1, meaning only tools with danger_level <= 1 execute without confirmation.

## Examples

```python
# Safe tool - read-only
class ListFilesTool(OrbitTool):
    name: str = "list_files"
    danger_level: int = 1  # Safe
    requires_confirmation: bool = False

# Moderate tool - writes data
class WriteFileTool(OrbitTool):
    name: str = "write_file"
    danger_level: int = 3  # Moderate
    requires_confirmation: bool = True  # Require confirmation

# Dangerous tool - deletes data
class DeletePathTool(OrbitTool):
    name: str = "delete_path"
    danger_level: int = 4  # Dangerous
    requires_confirmation: bool = True  # Always require confirmation
```
