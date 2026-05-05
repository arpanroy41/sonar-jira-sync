"""MCP server exposing SonarQube-JIRA sync tools."""

import json
from typing import Optional

from ..core import Config, SonarClient, JiraClient, distribute_issues, load_config


def create_mcp_server(config_path: Optional[str] = None):
    """Create and configure the MCP server with tools."""
    try:
        from fastmcp import FastMCP
    except ImportError:
        raise ImportError(
            "fastmcp is required for MCP server. Install with: pip install sonar-jira-sync[mcp]"
        )

    mcp = FastMCP("sonar-jira-sync")
    config: Optional[Config] = None

    def get_config() -> Config:
        nonlocal config
        if config is None:
            config = load_config(config_path)
        return config

    @mcp.tool()
    def fetch_issues(severities: Optional[str] = None) -> str:
        """Fetch open issues from SonarQube grouped by severity.

        Args:
            severities: Comma-separated severities to filter (e.g., "BLOCKER,CRITICAL,MAJOR").
                       If omitted, uses all configured severities.

        Returns:
            JSON with issues grouped by severity, including counts and details.
        """
        cfg = get_config()
        sev_list = severities.split(",") if severities else cfg.settings.severities

        with SonarClient(
            host=cfg.sonarqube.host,
            token=cfg.sonarqube.token,
            project_key=cfg.sonarqube.project_key,
        ) as client:
            grouped = client.fetch_issues_grouped(severities=sev_list)

        result = {
            "project_key": cfg.sonarqube.project_key,
            "total_issues": sum(len(v) for v in grouped.values()),
            "by_severity": {},
        }

        for severity, issues in grouped.items():
            result["by_severity"][severity] = {
                "count": len(issues),
                "issues": [
                    {
                        "key": i.key,
                        "rule": i.rule,
                        "message": i.message,
                        "file": i.file_path,
                        "line": i.line,
                        "type": i.type,
                        "effort": i.effort,
                    }
                    for i in issues
                ],
            }

        return json.dumps(result, indent=2)

    @mcp.tool()
    def preview_distribution(severities: Optional[str] = None) -> str:
        """Preview how issues would be distributed among teammates.

        Args:
            severities: Comma-separated severities to include (e.g., "CRITICAL,MAJOR").
                       If omitted, uses all configured severities.

        Returns:
            JSON showing assignment preview per teammate and severity.
        """
        cfg = get_config()
        sev_list = severities.split(",") if severities else cfg.settings.severities

        with SonarClient(
            host=cfg.sonarqube.host,
            token=cfg.sonarqube.token,
            project_key=cfg.sonarqube.project_key,
        ) as client:
            grouped = client.fetch_issues_grouped(severities=sev_list)

        plan = distribute_issues(grouped, cfg.teammates, severities=sev_list)

        result = {
            "total_issues": plan.total_issues,
            "teammates": [t.name for t in cfg.teammates],
            "distribution_summary": plan.summary(),
            "assignments_by_severity": {},
        }

        for severity, assignments in plan.by_severity.items():
            result["assignments_by_severity"][severity] = [
                {
                    "teammate": a.teammate.name,
                    "issue_key": a.issue.key,
                    "message": a.issue.message[:100],
                    "file": a.issue.file_path,
                }
                for a in assignments
            ]

        return json.dumps(result, indent=2)

    @mcp.tool()
    def create_jiras(severities: str, confirm: bool = False) -> str:
        """Create JIRA tickets for SonarQube issues, distributed among teammates.

        IMPORTANT: This creates real JIRA tickets. Only call after user explicitly approves.

        Args:
            severities: Comma-separated severities to create JIRAs for (e.g., "CRITICAL,MAJOR").
            confirm: Must be True to actually create tickets. If False, returns preview only.

        Returns:
            JSON with created ticket details or preview if confirm=False.
        """
        cfg = get_config()
        sev_list = severities.split(",")

        with SonarClient(
            host=cfg.sonarqube.host,
            token=cfg.sonarqube.token,
            project_key=cfg.sonarqube.project_key,
        ) as sonar:
            grouped = sonar.fetch_issues_grouped(severities=sev_list)

        plan = distribute_issues(grouped, cfg.teammates, severities=sev_list)

        if not confirm:
            return json.dumps({
                "mode": "DRY RUN - set confirm=True to create tickets",
                "would_create": plan.total_issues,
                "distribution": plan.summary(),
            }, indent=2)

        created = []
        errors = []

        with JiraClient(url=cfg.jira.url, email=cfg.jira.email, token=cfg.jira.token) as jira:
            for assignment in plan.assignments:
                try:
                    issue = jira.create_issue_from_sonar(
                        project_key=cfg.jira.project_key,
                        sonar_issue=assignment.issue,
                        sonar_host=cfg.sonarqube.host,
                        assignee_email=assignment.teammate.email,
                        issue_type=cfg.jira.issue_type,
                        labels=cfg.jira.labels,
                    )
                    created.append({
                        "jira_key": issue.key,
                        "url": issue.url,
                        "assignee": issue.assignee,
                        "priority": issue.priority,
                        "summary": issue.summary[:80],
                    })
                except Exception as e:
                    errors.append({
                        "sonar_key": assignment.issue.key,
                        "error": str(e),
                    })

        return json.dumps({
            "created": len(created),
            "failed": len(errors),
            "tickets": created,
            "errors": errors,
        }, indent=2)

    @mcp.tool()
    def get_config_info() -> str:
        """Show current configuration (without sensitive tokens)."""
        cfg = get_config()
        return json.dumps({
            "sonarqube": {
                "host": cfg.sonarqube.host,
                "project_key": cfg.sonarqube.project_key,
                "token_configured": bool(cfg.sonarqube.token),
            },
            "jira": {
                "url": cfg.jira.url,
                "project_key": cfg.jira.project_key,
                "issue_type": cfg.jira.issue_type,
                "labels": cfg.jira.labels,
                "credentials_configured": bool(cfg.jira.email and cfg.jira.token),
            },
            "teammates": [{"name": t.name, "email": t.email} for t in cfg.teammates],
            "settings": {
                "port": cfg.settings.port,
                "severities": cfg.settings.severities,
            },
        }, indent=2)

    return mcp
