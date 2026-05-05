"""SonarQube API client for fetching issues."""

from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class SonarIssue:
    key: str
    rule: str
    severity: str
    message: str
    component: str
    line: Optional[int]
    effort: Optional[str]
    type: str
    status: str

    @property
    def file_path(self) -> str:
        """Extract relative file path from component."""
        parts = self.component.split(":")
        return parts[-1] if len(parts) > 1 else self.component

    @property
    def sonar_url(self, host: str = "") -> str:
        return f"{host}/project/issues?id=&open={self.key}" if host else ""


class SonarClient:
    """Client for SonarQube REST API."""

    def __init__(self, host: str, token: str, project_key: str, verify_ssl: bool = False):
        self.host = host.rstrip("/")
        self.project_key = project_key
        self._client = httpx.Client(
            base_url=self.host,
            headers={"Authorization": f"Bearer {token}"},
            verify=verify_ssl,
            timeout=30.0,
        )

    def fetch_issues(
        self,
        severities: Optional[list[str]] = None,
        statuses: Optional[list[str]] = None,
        page_size: int = 500,
    ) -> list[SonarIssue]:
        """Fetch issues from SonarQube for the configured project."""
        params: dict = {
            "componentKeys": self.project_key,
            "ps": str(page_size),
            "statuses": ",".join(statuses or ["OPEN", "CONFIRMED", "REOPENED"]),
        }
        if severities:
            params["severities"] = ",".join(severities)

        all_issues: list[SonarIssue] = []
        page = 1

        while True:
            params["p"] = str(page)
            response = self._client.get("/api/issues/search", params=params)
            response.raise_for_status()
            data = response.json()

            for item in data.get("issues", []):
                all_issues.append(
                    SonarIssue(
                        key=item["key"],
                        rule=item["rule"],
                        severity=item["severity"],
                        message=item["message"],
                        component=item.get("component", ""),
                        line=item.get("line"),
                        effort=item.get("effort"),
                        type=item.get("type", "CODE_SMELL"),
                        status=item.get("status", "OPEN"),
                    )
                )

            total = data.get("total", 0)
            if page * page_size >= total:
                break
            page += 1

        return all_issues

    def fetch_issues_grouped(
        self, severities: Optional[list[str]] = None
    ) -> dict[str, list[SonarIssue]]:
        """Fetch issues and group them by severity."""
        issues = self.fetch_issues(severities=severities)
        grouped: dict[str, list[SonarIssue]] = {}
        for issue in issues:
            grouped.setdefault(issue.severity, []).append(issue)
        return grouped

    def get_issue_url(self, issue_key: str) -> str:
        """Get the web URL for a specific issue."""
        return (
            f"{self.host}/project/issues"
            f"?id={self.project_key}&open={issue_key}"
        )

    def get_severity_url(self, severity: str) -> str:
        """Get the web URL for all issues of a given severity."""
        return (
            f"{self.host}/project/issues"
            f"?impactSeverities={severity}"
            f"&issueStatuses=CONFIRMED%2COPEN"
            f"&id={self.project_key}"
        )

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
