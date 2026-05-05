"""Configuration loading and validation."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class Teammate:
    name: str
    email: str


@dataclass
class SonarConfig:
    host: str
    project_key: str
    token: str = ""

    def __post_init__(self):
        self.token = self.token or os.environ.get("SONAR_TOKEN", "")


@dataclass
class JiraConfig:
    url: str
    project_key: str
    issue_type: str = "Bug"
    labels: list[str] = field(default_factory=lambda: ["sonarqube", "code-quality"])
    email: str = ""
    token: str = ""

    def __post_init__(self):
        self.email = self.email or os.environ.get("JIRA_EMAIL", "")
        self.token = self.token or os.environ.get("JIRA_TOKEN", "")


@dataclass
class Settings:
    port: int = 8090
    severities: list[str] = field(
        default_factory=lambda: ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]
    )


@dataclass
class Config:
    sonarqube: SonarConfig
    jira: JiraConfig
    teammates: list[Teammate]
    settings: Settings

    def validate(self) -> list[str]:
        """Return list of validation errors, empty if valid."""
        errors = []
        if not self.sonarqube.host:
            errors.append("sonarqube.host is required")
        if not self.sonarqube.project_key:
            errors.append("sonarqube.project_key is required")
        if not self.sonarqube.token:
            errors.append("SONAR_TOKEN env var is required")
        if not self.jira.url:
            errors.append("jira.url is required")
        if not self.jira.project_key:
            errors.append("jira.project_key is required")
        if not self.jira.email:
            errors.append("JIRA_EMAIL env var is required")
        if not self.jira.token:
            errors.append("JIRA_TOKEN env var is required")
        if not self.teammates:
            errors.append("At least one teammate is required")
        return errors


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML file."""
    path = Path(config_path) if config_path else Path("config.yaml")

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    sonar = SonarConfig(
        host=raw.get("sonarqube", {}).get("host", ""),
        project_key=raw.get("sonarqube", {}).get("project_key", ""),
    )

    jira = JiraConfig(
        url=raw.get("jira", {}).get("url", ""),
        project_key=raw.get("jira", {}).get("project_key", ""),
        issue_type=raw.get("jira", {}).get("issue_type", "Bug"),
        labels=raw.get("jira", {}).get("labels", ["sonarqube", "code-quality"]),
    )

    teammates = [
        Teammate(name=t["name"], email=t["email"])
        for t in raw.get("teammates", [])
    ]

    settings_raw = raw.get("settings", {})
    settings = Settings(
        port=settings_raw.get("port", 8090),
        severities=settings_raw.get(
            "severities", ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]
        ),
    )

    return Config(sonarqube=sonar, jira=jira, teammates=teammates, settings=settings)
