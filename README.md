# Claudette

<div align="center">

**A powerful CLI chatbot powered by Ollama with advanced tool support**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## 🚀 Overview

Claudette is an advanced command-line chatbot interface for Ollama that brings LLM capabilities to your terminal with a rich set of features including:

- 🎨 **Beautiful Terminal UI** with Rich rendering
- 🔧 **Tool Support** - File operations, web search, command execution
- 🧠 **Advanced Reasoning** - Support for thinking/reasoning models (DeepSeek-R1, etc.)
- 💬 **Conversation Management** - Save, load, and manage multiple conversations
- 📊 **Usage Statistics** - Track token usage and performance metrics
- 🎯 **Smart Reprompting** - Automatically optimize user prompts for better LLM comprehension
- 🖼️ **Vision Support** - Multi-modal capabilities for models with vision
- ⚙️ **Highly Configurable** - Per-model system prompts, temperature control, validation modes

---

## ✨ Features

### 💻 Rich Terminal Interface

- **Live Streaming Responses** with animated thinking indicators
- **Syntax Highlighting** for code blocks with Markdown rendering
- **Interactive Bottom Toolbar** showing:
  - Current working directory
  - Git branch
  - Model name and capabilities
  - Vision/Tools/Thinking mode status
  - Temperature setting
  - Token usage with percentage
- **Auto-completion** for commands and file paths
- **Multi-line Input** support (Alt+Enter for new lines)
- **Conversation History** with persistent storage

### 🛠️ Built-in Tools

Claudette provides LLMs with access to powerful tools:

| Tool | Description |
|------|-------------|
| **read_file** | Read file contents from the filesystem |
| **write_file** | Create or overwrite files |
| **edit_file** | Make targeted edits to existing files |
| **execute_command** | Run shell commands with safety confirmations |
| **list_directory** | Browse directory contents |
| **web_search** | Search the web using DuckDuckGo |
| **ask_user** | Request clarification or additional information from the user |
| **get_current_time** | Retrieve current date and time |

All tools include **optional user confirmation** for safety.

### 📋 Commands

Claudette supports a comprehensive set of commands:

| Command | Description |
|---------|-------------|
| `/clear` | Clear conversation history |
| `/conversations` | List all saved conversations |
| `/exit`, `/quit` | Exit the application |
| `/history` | Display conversation history |
| `/info <model>` | Show detailed model information |
| `/init` | Initialize configuration in current directory |
| `/load <name>` | Load a saved conversation |
| `/model <name>` | Switch to a different model |
| `/models`, `/list` | List all available models |
| `/prompt` | Display current system prompt |
| `/pull <model>` | Download a new model from Ollama |
| `/reprompting` | Toggle auto-reprompting mode |
| `/save [name]` | Save current conversation |
| `/stats` | Display usage statistics |
| `/temperature <value>` | Set temperature (0.0-1.0) |
| `/thinking` | Toggle thinking/reasoning mode |
| `/unload` | Unload current model from memory |
| `/validate` | Toggle tool validation mode |

### 🧠 Advanced Features

#### Thinking/Reasoning Mode
Enable extended reasoning for compatible models (DeepSeek-R1, QwQ, etc.):
```bash
/thinking
```
Models will show their internal thought process before providing answers, with automatic detection of circular reasoning.

#### Smart Reprompting
Automatically optimize user messages for better LLM comprehension:
```bash
/reprompting
```
Claudette will rewrite vague prompts to be more explicit and contextual.

#### Conversation Management
Save and load conversations for later reference:
```bash
/save my_conversation
/load my_conversation
/conversations  # List all saved conversations
```

#### Usage Statistics
Track token usage, execution time, and costs per model:
```bash
/stats
```

---

## 📦 Installation

### Prerequisites

- **Python 3.8+**
- **Ollama** ([Install Ollama](https://ollama.ai))

### Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd claudette
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Ollama is running**
   ```bash
   ollama --version
   ollama serve  # If not already running
   ```

4. **Pull a model** (if you haven't already)
   ```bash
   ollama pull qwen3:4b
   ```

---

## 🎯 Quick Start

### Basic Usage

```bash
# Use default model (qwen3-coder:30b)
python main.py

# Specify a model
python main.py --model deepseek-r1:7b

# Connect to remote Ollama instance
python main.py --host http://192.168.1.100:11434

# Combine options
python main.py --model qwen2.5-coder:14b --host http://localhost:11434
```

### Command-Line Options

```
Options:
  -m, --model MODEL    Model name to use (default: qwen3-coder:30b)
  -H, --host HOST      Ollama host URL (default: http://localhost:11434)
  -h, --help          Show help message
```

---

## ⚙️ Configuration

### Model Configuration

Claudette uses YAML configuration files for per-model customization. Create a file at:
- `.claudette/models_config.yaml` (local to project), or
- `~/.claudette/models_config.yaml` (global)

**Example configuration:**

```yaml
models:
  qwen3-coder:30b:
    system_prompt: |
      You are an expert coding assistant specialized in Python, JavaScript, and system design.
      Always explain your reasoning and provide production-ready code.
    enable_tools: true

  deepseek-r1:7b:
    system_prompt: |
      You are a reasoning assistant. Think step-by-step and show your thought process.
    enable_tools: false

common_prompts:
  tool_usage_protocol: |
    When using tools:
    - Explain what you're about to do before calling the tool
    - Verify the result after execution
    - Ask for confirmation on destructive operations

  verification_protocol: |
    Always verify:
    - File paths exist before reading/writing
    - Commands are safe before execution
    - Web search results are relevant
```

### Initialize Configuration

Create a local configuration for your project:

```bash
python main.py
> /init
```

This creates `.claudette/models_config.yaml` with sensible defaults.

---

## 🎨 Usage Examples

### Basic Chat

```
> What is a closure in JavaScript?

● 2.3s · 245 tokens

A closure is a function that has access to variables in its outer (enclosing)
function's scope, even after the outer function has returned...
```

### Using Tools

```
> Create a Python script that prints "Hello, World!"

▸ write_file
  path: "hello.py"
  content: "print('Hello, World!')"

✓ completed
  📄 Output preview: File successfully written to hello.py

The script has been created at `hello.py`.
```

### Reasoning Mode

```
> /thinking
✓ Thinking mode enabled 🧠

> Solve: If a train travels 120km in 2 hours, how fast is it going?

💭 Thinking Process
Let me work through this step by step...
First, I need to identify what we're looking for: speed
Speed = Distance / Time
Distance = 120 km
Time = 2 hours
Therefore: Speed = 120 / 2 = 60 km/h

● 4.1s · 89 tokens · 🧠 234 thinking tokens

The train is traveling at 60 km/h.
```

### Vision Mode (with compatible models)

```
> @screenshot.png What's in this image?

▸ vision: 1 image(s) attached

● 3.2s · 156 tokens

The image shows a terminal window with code highlighting...
```

---

## 🏗️ Project Structure

```
claudette/
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── README.md                    # This file
│
├── src/
│   ├── __init__.py
│   ├── chatbot.py              # Main ChatBot class
│   ├── models.py               # Model abstraction and factory
│   ├── tools.py                # Tool executor
│   ├── ui.py                   # Rich terminal UI components
│   ├── config.py               # Configuration management
│   ├── image_utils.py          # Vision/image handling
│   ├── completers.py           # Auto-completion logic
│   │
│   ├── commands/               # Command implementations
│   │   ├── base.py
│   │   ├── manager.py
│   │   ├── clear_command.py
│   │   ├── model_command.py
│   │   ├── thinking_command.py
│   │   └── ...
│   │
│   ├── tools_impl/             # Tool implementations
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── read_file_tool.py
│   │   ├── write_file_tool.py
│   │   ├── execute_command_tool.py
│   │   ├── web_search_tool.py
│   │   └── ...
│   │
│   └── utils/                  # Utility modules
│       ├── stats.py            # Statistics tracking
│       ├── conversation.py     # Conversation management
│       └── git.py              # Git integration
│
└── .claudette/                 # Local configuration
    ├── models_config.yaml      # Model configurations
    └── conversations/          # Saved conversations
```

---

## 🔧 Development

### Code Style

This project uses [Black](https://github.com/psf/black) for code formatting:

```bash
black main.py src/
```

### Type Hints

Claudette uses comprehensive type hints throughout the codebase for better IDE support and code clarity.

### Testing

```bash
# Run tests (if available)
pytest tests/
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines (enforced by Black)
- Add type hints to all functions
- Write docstrings for public APIs
- Test your changes thoroughly
- Update documentation as needed

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[Ollama](https://ollama.ai)** - Local LLM runtime
- **[Rich](https://github.com/Textualize/rich)** - Beautiful terminal formatting
- **[Prompt Toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit)** - Interactive CLI framework
- **Community** - Thanks to all contributors and users!

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/claudette/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/claudette/discussions)

---

<div align="center">

**Made with ❤️ by the Claudette Team**

⭐ Star us on GitHub if you find this project useful!

</div>
