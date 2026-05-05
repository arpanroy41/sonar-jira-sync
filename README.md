# sonar-jira-sync

[![PyPI version](https://badge.fury.io/py/sonar-jira-sync.svg)](https://pypi.org/project/sonar-jira-sync/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Pull SonarQube issues, review them in a local web UI, and create JIRA tickets distributed equally among your team.

## Features

- **Fetch issues** from SonarQube, grouped by severity
- **Equal distribution** of tickets among teammates (round-robin within each severity)
- **Local web UI** for reviewing issues and approving ticket creation
- **CLI** with summary and interactive mode
- **MCP server** for AI assistant integration (Cursor, Claude, etc.)

## Installation

```bash
pip install sonar-jira-sync
```

For MCP server support:
```bash
pip install sonar-jira-sync[mcp]
```

> **Note:** If you get `command not found: sonar-jira-sync` after install, your Python scripts directory may not be on PATH. Add it:
> ```bash
> # Find where pip installed the script
> pip show -f sonar-jira-sync | grep "Location"
>
> # Add to ~/.zshrc (macOS) or ~/.bashrc (Linux) — example for macOS:
> echo 'export PATH="/Library/Frameworks/Python.framework/Versions/3.12/bin:$PATH"' >> ~/.zshrc
> source ~/.zshrc
> ```
> Alternatively, use `pipx install sonar-jira-sync` which handles PATH automatically.

## Quick Start

1. Copy and customize the config:
```bash
cp config.example.yaml config.yaml
```

2. Create a `.env` file with your credentials:
```bash
SONAR_TOKEN=your-sonarqube-token
JIRA_EMAIL=your-email@company.com
JIRA_TOKEN="your-jira-api-token"
```

> **Note:** If your token contains special characters like `=`, wrap it in double quotes.

3. Source the `.env` and run:
```bash
set -a && source .env && set +a
sonar-jira-sync run
```

Or get a CLI summary:
```bash
sonar-jira-sync summary
```

> **Tip:** You must source `.env` in each new terminal session, or add `set -a && source /path/to/.env && set +a` to your `~/.zshrc` for persistence.

## Usage

### CLI Commands

| Command | Description |
|---------|-------------|
| `sonar-jira-sync run` | Launch web UI for interactive review |
| `sonar-jira-sync summary` | Show issues and distribution preview |
| `sonar-jira-sync summary -s CRITICAL,MAJOR` | Filter by severity |
| `sonar-jira-sync mcp` | Start MCP server |

### MCP Integration

Add to your Cursor MCP config (`~/.cursor/mcp.json`):

```json
{
  "sonar-jira-sync": {
    "command": "sonar-jira-sync",
    "args": ["mcp", "-c", "/path/to/config.yaml"],
    "env": {
      "SONAR_TOKEN": "your-sonarqube-token",
      "JIRA_EMAIL": "your-email@company.com",
      "JIRA_TOKEN": "your-jira-api-token"
    }
  }
}
```

> **Note:** If `sonar-jira-sync` is not on your PATH, use the full path to the binary:
> ```json
> "command": "/Library/Frameworks/Python.framework/Versions/3.12/bin/sonar-jira-sync"
> ```
> Find it with: `which sonar-jira-sync` or `pip show -f sonar-jira-sync`

Available MCP tools:
- `fetch_issues` - Get SonarQube issues grouped by severity
- `preview_distribution` - Preview ticket distribution among teammates
- `create_jiras` - Create JIRA tickets (requires explicit confirmation)
- `get_config_info` - Show current configuration

## Configuration

See `config.example.yaml` for all options. Sensitive values (tokens) are loaded from environment variables:

| Variable | Purpose |
|----------|---------|
| `SONAR_TOKEN` | SonarQube authentication token |
| `JIRA_EMAIL` | JIRA account email |
| `JIRA_TOKEN` | JIRA API token |

## Publishing to PyPI

Build and upload:
```bash
pip install build twine
python -m build
twine upload dist/*
```

## Contributing

1. Clone the repo:
```bash
git clone https://github.com/arpanroy41/sonar-jira-sync.git
cd sonar-jira-sync
```

2. Install in development mode:
```bash
pip install -e ".[dev]"
```

3. Run tests:
```bash
pytest
```

## License

MIT

## Author

[arpanroy41](https://github.com/arpanroy41)
