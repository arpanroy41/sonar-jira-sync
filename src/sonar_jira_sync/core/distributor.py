"""Distribution logic for assigning issues to teammates."""

from dataclasses import dataclass, field

from .config import Teammate
from .sonar_client import SonarIssue


@dataclass
class Assignment:
    teammate: Teammate
    issue: SonarIssue


@dataclass
class DistributionPlan:
    """Preview of how issues will be distributed."""
    assignments: list[Assignment] = field(default_factory=list)
    by_severity: dict[str, list[Assignment]] = field(default_factory=dict)
    by_teammate: dict[str, list[Assignment]] = field(default_factory=dict)

    @property
    def total_issues(self) -> int:
        return len(self.assignments)

    def summary(self) -> dict[str, dict[str, int]]:
        """Return count of issues per teammate per severity."""
        result: dict[str, dict[str, int]] = {}
        for assignment in self.assignments:
            name = assignment.teammate.name
            severity = assignment.issue.severity
            result.setdefault(name, {}).setdefault(severity, 0)
            result[name][severity] += 1
        return result


def distribute_issues(
    issues_by_severity: dict[str, list[SonarIssue]],
    teammates: list[Teammate],
    severities: list[str] | None = None,
) -> DistributionPlan:
    """
    Distribute issues equally within each severity level using round-robin.

    Args:
        issues_by_severity: Issues grouped by severity from SonarClient.
        teammates: List of teammates to distribute among.
        severities: Which severities to include (None = all).

    Returns:
        DistributionPlan with all assignments.
    """
    if not teammates:
        raise ValueError("At least one teammate required for distribution")

    plan = DistributionPlan()
    severity_order = severities or ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]

    for severity in severity_order:
        issues = issues_by_severity.get(severity, [])
        if not issues:
            continue

        severity_assignments: list[Assignment] = []

        for idx, issue in enumerate(issues):
            teammate = teammates[idx % len(teammates)]
            assignment = Assignment(teammate=teammate, issue=issue)
            severity_assignments.append(assignment)
            plan.assignments.append(assignment)

            plan.by_teammate.setdefault(teammate.name, []).append(assignment)

        plan.by_severity[severity] = severity_assignments

    return plan
