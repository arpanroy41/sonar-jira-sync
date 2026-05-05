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

## Quick Start

1. Copy and customize the config:
```bash
cp config.example.yaml config.yaml
```

2. Set environment variables:
```bash
export SONAR_TOKEN="your-sonarqube-token"
export JIRA_EMAIL="your-email@company.com"
export JIRA_TOKEN="your-jira-api-token"
```

3. Run the web UI:
```bash
sonar-jira-sync run
```

Or get a CLI summary:
```bash
sonar-jira-sync summary
```

## Usage

### CLI Commands

| Command | Description |
|---------|-------------|
| `sonar-jira-sync run` | Launch web UI for interactive review |
| `sonar-jira-sync summary` | Show issues and distribution preview |
| `sonar-jira-sync summary -s CRITICAL,MAJOR` | Filter by severity |
| `sonar-jira-sync mcp` | Start MCP server |

### MCP Integration

Add to your Cursor MCP config:

```json
{
  "sonar-jira-sync": {
    "command": "sonar-jira-sync",
    "args": ["mcp", "-c", "/path/to/config.yaml"]
  }
}
```

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
