# Update Docs Command

Keep documentation in sync with code.

## Usage

```
/update-docs
/update-docs --api      # Update API docs only
/update-docs --arch     # Update architecture docs
```

## What Gets Updated

1. **CLAUDE.md** - Project instructions
2. **README.md** - Usage and setup
3. **API docs** - Endpoint documentation
4. **Architecture** - System design docs

## Example Output

```markdown
# Documentation Update Report

## Updated Files

### CLAUDE.md
- Added new LLM provider (GLM)
- Updated graph structure diagram
- Added safety layer documentation

### docs/API.md
- Added POST /api/v1/chat endpoint
- Updated session management endpoints
- Added error response formats

### docs/ARCHITECTURE.md
- Updated state flow diagram
- Added memory management section
- Updated LLM routing logic

## Suggestions

1. Consider adding sequence diagrams for complex flows
2. Add examples to API documentation
3. Document environment variables in README
```
