"""Flask application for reviewing SonarQube issues and approving JIRA creation."""

import json
from pathlib import Path

from flask import Flask, render_template, request, jsonify

from ..core import Config, SonarClient, JiraClient, distribute_issues
from ..core.distributor import DistributionPlan


def create_app(config: Config) -> Flask:
    """Create Flask app with the given configuration."""
    template_dir = Path(__file__).parent / "templates"
    app = Flask(__name__, template_folder=str(template_dir))
    app.config["SECRET_KEY"] = "sonar-jira-sync-local"

    plan_cache: dict[str, DistributionPlan] = {}

    @app.route("/")
    def index():
        return render_template("index.html", config=config)

    @app.route("/api/fetch-issues", methods=["POST"])
    def api_fetch_issues():
        data = request.get_json() or {}
        severities = data.get("severities", config.settings.severities)

        try:
            with SonarClient(
                host=config.sonarqube.host,
                token=config.sonarqube.token,
                project_key=config.sonarqube.project_key,
            ) as client:
                grouped = client.fetch_issues_grouped(severities=severities)

            plan = distribute_issues(grouped, config.teammates, severities=severities)
            plan_cache["current"] = plan

            result = {
                "total_issues": plan.total_issues,
                "summary": plan.summary(),
                "by_severity": {},
            }

            for severity, assignments in plan.by_severity.items():
                result["by_severity"][severity] = [
                    {
                        "teammate": a.teammate.name,
                        "teammate_email": a.teammate.email,
                        "issue_key": a.issue.key,
                        "rule": a.issue.rule,
                        "message": a.issue.message,
                        "file": a.issue.file_path,
                        "line": a.issue.line,
                        "type": a.issue.type,
                        "effort": a.issue.effort,
                        "url": config.sonarqube.host
                        + f"/project/issues?id={config.sonarqube.project_key}&open={a.issue.key}",
                    }
                    for a in assignments
                ]

            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/create-jiras", methods=["POST"])
    def api_create_jiras():
        data = request.get_json() or {}
        approved_list = data.get("approved", [])

        plan = plan_cache.get("current")
        if not plan:
            return jsonify({"error": "No distribution plan. Fetch issues first."}), 400

        if not approved_list:
            return jsonify({"error": "No issues approved for JIRA creation."}), 400

        override_map = {item["key"]: item.get("assignee_email") for item in approved_list}
        approved_keys = set(override_map.keys())

        assignments_to_create = [
            a for a in plan.assignments if a.issue.key in approved_keys
        ]

        created = []
        errors = []

        with JiraClient(
            url=config.jira.url, email=config.jira.email, token=config.jira.token
        ) as jira:
            for assignment in assignments_to_create:
                assignee = override_map.get(
                    assignment.issue.key, assignment.teammate.email
                )
                try:
                    issue = jira.create_issue_from_sonar(
                        project_key=config.jira.project_key,
                        sonar_issue=assignment.issue,
                        sonar_host=config.sonarqube.host,
                        assignee_email=assignee,
                        issue_type=config.jira.issue_type,
                        labels=config.jira.labels,
                    )
                    created.append({
                        "jira_key": issue.key,
                        "url": issue.url,
                        "assignee": issue.assignee,
                        "priority": issue.priority,
                        "summary": issue.summary,
                    })
                except Exception as e:
                    errors.append({
                        "sonar_key": assignment.issue.key,
                        "error": str(e),
                    })

        return jsonify({
            "created": len(created),
            "failed": len(errors),
            "tickets": created,
            "errors": errors,
        })

    return app


def run_web(config: Config):
    """Launch the Flask web server."""
    app = create_app(config)
    print(f"\n  SonarQube-JIRA Sync UI running at: http://localhost:{config.settings.port}\n")
    app.run(host="0.0.0.0", port=config.settings.port, debug=False)
