# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ IMPORTANT: Git Branch Policy

**Branch Naming Constraint**: Claude Code can only push to branches ending with the current session ID.

**Development Branch**: `claude/developpement-0157HNsrYJv3uYsHdcEi2fuL`

**Workflow**:
1. Claude creates session branches: `claude/<description>-<sessionID>`
2. Claude pushes all changes to the session branch
3. User merges session branch into `claude/developpement-0157HNsrYJv3uYsHdcEi2fuL` using scripts
4. User can clean up old session branches after merging

**Scripts Available**:
- `scripts/fusionne.sh` or `scripts/fusionne.ps1` - Merge session branch into development
- `scripts/nettoyer-branches.sh` or `scripts/nettoyer-branches.ps1` - Clean up old branches

**Usage**:
```bash
# Ubuntu/Linux - Merge Claude's work (preserves current branch)
./scripts/fusionne.sh claude/fix-safe-directory-warning-01MdoVv6j7to7ph4yW1cw7wf

# PowerShell - Merge Claude's work
.\scripts\fusionne.ps1 claude/fix-safe-directory-warning-01MdoVv6j7to7ph4yW1cw7wf

# Clean up old branches
./scripts/nettoyer-branches.sh
.\scripts\nettoyer-branches.ps1
```

## Application Overview

OllamaTrad is a Python application for intelligent processing of JSON files using multiple AI providers (Ollama, OpenAI, Mistral, Anthropic). It provides both CLI and GUI interfaces for tasks like translation, content processing, metadata management, and direct AI dialogue with a file system-like navigation approach for JSON structures.

## Running the Application

```bash
# Install dependencies
pip install json5 requests aiohttp

# Run CLI mode (default)
python ollamaTrad.py

# Run GUI mode
python ollamaTrad.py --gui

# Load a file directly
python ollamaTrad.py --file data.json

# Execute a command directly
python ollamaTrad.py --command "translate /title fr"
python ollamaTrad.py --command "ia 'Hello AI'"
python ollamaTrad.py --command "/show"
```

## Architecture Overview

### Core Components

- **ollamaTrad.py**: Entry point with argument parsing for CLI/GUI modes
- **core/json_manager.py**: JSON navigation system treating structures as filesystems with JsonPath class
- **core/ai_client.py**: Unified AI client supporting multiple providers (Ollama, OpenAI, Mistral, Anthropic)
- **core/ollama_client.py**: Original Ollama-specific client (legacy)
- **core/metadata.py**: File metadata management with tags and context (legacy)
- **core/operation_history.py**: Advanced operation history with undo/redo capabilities
- **core/i18n.py**: Complete internationalization system supporting French, English, Spanish, German, Italian
- **cli/commands.py**: Command-line interface with comprehensive command set
- **gui/app.py**: Tkinter-based GUI with streamlined workflow and provider configuration
- **config/settings.json**: Multi-provider configuration with API keys and settings
- **translations/**: External translation files for each supported language

### Key Features

#### 1. Multi-Provider AI Support
- **Ollama** (local): Default provider with full native command support
- **OpenAI**: GPT models with API key configuration
- **Mistral AI**: Mistral models with API integration
- **Anthropic**: Claude models support

#### 2. Direct AI Dialogue
```bash
# CLI
ia "How can I improve this translation?"
provider set openai
ia "Compare this with the previous result"

# GUI
/ia How can I improve this translation?
ia Compare this with the previous result
```

#### 3. Internal Commands (Ollama-inspired)
```bash
/show                    # Display provider/model information
/set temperature 0.7     # Set session variables
/load model_name         # Change current model
/clear                   # Clear conversation history
/save session_name       # Save current session
/help                    # Internal commands help
```

#### 4. Advanced Translation System
```bash
# New command format: translate -language path
translate -fr book/title                    # Standard translation
translate -fr -add book/title               # Keep original + translation
translate -fr -plus book/title              # Translation + original
translate -fr book                          # Recursive translation of all text fields
```

#### 5. Operation History with Undo/Redo
- Complete operation tracking with before/after snapshots
- Navigate to any point in operation history
- Detailed metadata for each operation
- Session persistence and restoration

### File Structure

```
ollamaFic/
├── ollamaTrad.py                     # Entry point
├── core/
│   ├── json_manager.py         # JSON navigation and modification
│   ├── ai_client.py           # Multi-provider AI client
│   ├── ollama_client.py       # Legacy Ollama client
│   ├── metadata.py            # Legacy metadata system
│   ├── operation_history.py   # Advanced operation history
│   └── i18n.py               # Internationalization
├── cli/
│   └── commands.py            # Command-line interface
├── gui/
│   └── app.py                # Graphical interface
├── config/
│   └── settings.json         # Multi-provider configuration
├── translations/
│   ├── fr.json               # French translations
│   ├── en.json               # English translations
│   ├── es.json               # Spanish translations
│   ├── de.json               # German translations
│   └── it.json               # Italian translations
├── data/                     # User data directory
│   ├── metadata/             # File metadata
│   ├── sessions/             # Legacy sessions
│   ├── history/              # Operation history
│   └── snapshots/            # Operation snapshots
└── conversations/            # Saved conversations
```

## Key Commands

### File Management
```bash
load <file>                  # Load JSON file
save [file]                 # Save JSON file
ls [path]                   # List JSON path contents
cat <path>                  # Display JSON path content
search <pattern>            # Search in JSON
```

### AI Operations
```bash
translate -fr <path>        # Translate to French
translate -en -add <path>   # Translate to English, keep original
process <path> "instruction" # Process with custom instruction
ia "message"                # Direct AI dialogue
```

### Provider Management
```bash
provider list               # List available providers
provider set ollama         # Switch to Ollama
provider set openai         # Switch to OpenAI
provider clear              # Clear conversation history
provider history            # Show conversation history
```

### Internal Commands
```bash
/show                       # Provider information
/set var value              # Set session variable
/load model                 # Change model
/clear                      # Clear conversation
/save name                  # Save session
/help                       # Internal help
```

### Session Management
```bash
session start [model]       # Start processing session
session end                 # End current session
tag add <tag>              # Add tag to file
context "text"             # Set file context
```

## Configuration

### Multi-Provider Setup (config/settings.json)
```json
{
  "ai_providers": {
    "default_provider": "ollama",
    "ollama": {
      "host": "http://localhost:11434",
      "default_model": "aya"
    },
    "openai": {
      "api_key": "sk-...",
      "default_model": "gpt-4"
    },
    "mistral": {
      "api_key": "...",
      "default_model": "mistral-large-latest"
    },
    "anthropic": {
      "api_key": "sk-ant-...",
      "default_model": "claude-3-sonnet-20240229"
    }
  }
}
```

## GUI Features

### Interface Layout
- **Left Panel**: JSON tree navigation with color coding
  - Red: Modified, unsaved
  - Orange: Extended (add/plus) after save
  - Green: Modified and saved
- **Right Panel**: Split between work area and chat
- **Resizable**: PanedWindow for flexible layout

### Provider Configuration
- Click **🤖 Providers** button for configuration interface
- Tabbed interface for each provider
- API key management with masking
- Real-time connection status
- Conversation history viewer

### Visual Feedback
- Color-coded tree elements showing modification state
- Real-time status updates
- Progress indicators for batch operations
- Chat interface with command history

## Operation History System

### Key Features
- **Complete Tracking**: Every operation recorded with before/after snapshots
- **Undo/Redo**: Navigate backwards and forwards in operation history
- **Jump Navigation**: Go directly to any previous state
- **Session Persistence**: History saved and restorable
- **Detailed Metadata**: Timestamps, providers, session variables, execution time

### Usage
```python
# The system automatically tracks all operations
# Manual navigation available through GUI or programmatically

# Undo last operation
undo_info = history_manager.undo_last_operation()

# Redo next operation
redo_info = history_manager.redo_next_operation()

# Jump to specific operation
changes = history_manager.jump_to_operation("op_1634567890_5")

# Get history overview
history = history_manager.get_operation_history(limit=20)
```

## Development Guidelines

### Adding New Commands
1. Add command parsing in `cli/commands.py:parse_and_execute()`
2. Implement command method following pattern `cmd_<name>()`
3. Update help text in `cmd_help()`
4. Add GUI support in `gui/app.py:execute_chat_command()` if needed

### Adding New Providers
1. Create provider class inheriting from `AIProvider` in `core/ai_client.py`
2. Implement required methods: `chat()`, `check_connection()`
3. Override internal commands methods as needed: `cmd_show()`, `cmd_load()`, etc.
4. Add provider configuration in `config/settings.json`
5. Update GUI configuration interface

### Operation History Integration
1. Use `OperationHistoryManager` instead of legacy `MetadataManager`
2. Record operations with `record_operation()` including before/after data
3. Provide undo/redo functionality in interface
4. Use session variables for contextual operations

### Internationalization
1. Add translation keys in `core/i18n.py`
2. Create corresponding JSON files in `translations/`
3. Use `_("key")` function for translatable strings
4. Test with different locales: `set_locale("es")`

## Testing

### Test Files
- Create JSON test files in the project root for testing
- Use `test_*.json` naming convention
- Clean up test files after use

### Common Test Scenarios
```bash
# Test basic functionality
python main.py --file test.json --command "ls"

# Test translation
python main.py --file test.json --command "translate -fr /title"

# Test provider switching
python main.py --file test.json --command "provider set openai"

# Test internal commands
python main.py --file test.json --command "/show"

# Test GUI
python main.py --gui --file test.json
```

### Key Test Areas
- Multi-provider AI communication
- JSON navigation and modification
- Operation history and undo/redo
- Translation with recursive processing
- Internal commands across providers
- GUI provider configuration
- Internationalization switching

## Error Handling

- Graceful degradation when providers are unavailable
- Comprehensive error messages with context
- Recovery suggestions for common issues
- Operation rollback on failure
- Session state preservation

## Performance Considerations

- Async operations for non-blocking AI calls
- Threading for GUI responsiveness
- Memory management for large operation histories
- Efficient JSON navigation for large files
- Lazy loading of provider configurations

This architecture provides a robust foundation for AI-assisted JSON processing with comprehensive provider support, detailed operation tracking, and professional workflow capabilities.