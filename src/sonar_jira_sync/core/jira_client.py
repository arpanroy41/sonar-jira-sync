"""JIRA API client for creating tickets and resolving users."""

from dataclasses import dataclass
from typing import Optional

import httpx


SEVERITY_PRIORITY_MAP = {
    "BLOCKER": "Blocker",
    "CRITICAL": "Critical",
    "MAJOR": "Major",
    "MINOR": "Minor",
    "INFO": "Trivial",
}


@dataclass
class CreatedIssue:
    key: str
    summary: str
    assignee: str
    priority: str
    url: str


class JiraClient:
    """Client for JIRA REST API."""

    def __init__(self, url: str, email: str, token: str):
        self.url = url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.url,
            auth=(email, token),
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )
        self._account_cache: dict[str, str] = {}

    def resolve_account_id(self, email: str) -> Optional[str]:
        """Look up a JIRA account ID by email."""
        if email in self._account_cache:
            return self._account_cache[email]

        response = self._client.get(
            "/rest/api/2/user/search", params={"query": email}
        )
        response.raise_for_status()
        users = response.json()

        if users:
            account_id = users[0].get("accountId")
            self._account_cache[email] = account_id
            return account_id
        return None

    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Bug",
        priority: str = "Major",
        assignee_email: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> CreatedIssue:
        """Create a JIRA issue."""
        fields: dict = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
        }

        if labels:
            fields["labels"] = labels

        if assignee_email:
            account_id = self.resolve_account_id(assignee_email)
            if account_id:
                fields["assignee"] = {"accountId": account_id}

        response = self._client.post("/rest/api/2/issue", json={"fields": fields})
        response.raise_for_status()
        data = response.json()

        issue_key = data["key"]
        return CreatedIssue(
            key=issue_key,
            summary=summary,
            assignee=assignee_email or "Unassigned",
            priority=priority,
            url=f"{self.url}/browse/{issue_key}",
        )

    def create_issue_from_sonar(
        self,
        project_key: str,
        sonar_issue,
        sonar_host: str,
        assignee_email: Optional[str] = None,
        issue_type: str = "Bug",
        labels: Optional[list[str]] = None,
    ) -> CreatedIssue:
        """Create a JIRA issue from a SonarQube issue object."""
        priority = SEVERITY_PRIORITY_MAP.get(sonar_issue.severity, "Major")
        sonar_url = f"{sonar_host}/project/issues?id={project_key}&open={sonar_issue.key}"

        summary = f"[SonarQube] {sonar_issue.message[:200]}"
        description = (
            f"*SonarQube Issue*\n\n"
            f"||Field||Value||\n"
            f"|Rule|{sonar_issue.rule}|\n"
            f"|Severity|{sonar_issue.severity}|\n"
            f"|Type|{sonar_issue.type}|\n"
            f"|File|{sonar_issue.file_path}|\n"
            f"|Line|{sonar_issue.line or 'N/A'}|\n"
            f"|Effort|{sonar_issue.effort or 'N/A'}|\n\n"
            f"*Message:* {sonar_issue.message}\n\n"
            f"[View in SonarQube|{sonar_url}]"
        )

        return self.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type=issue_type,
            priority=priority,
            assignee_email=assignee_email,
            labels=labels,
        )

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
