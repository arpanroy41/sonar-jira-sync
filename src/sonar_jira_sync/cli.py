"""CLI entry point for sonar-jira-sync."""

import click
from rich.console import Console
from rich.table import Table

from .core import load_config, SonarClient, distribute_issues

console = Console()


@click.group()
@click.option("--config", "-c", default="config.yaml", help="Path to config file.")
@click.pass_context
def main(ctx, config):
    """SonarQube-to-JIRA Sync Tool: fetch issues, review, and create tickets."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config


@main.command()
@click.option("--config", "-c", default=None, help="Path to config file.")
@click.pass_context
def run(ctx, config):
    """Launch the web UI for interactive review and approval."""
    cfg = load_config(config or ctx.obj["config_path"])
    errors = cfg.validate()
    if errors:
        for err in errors:
            console.print(f"[red]Config error:[/] {err}")
        raise SystemExit(1)

    from .web.app import run_web

    run_web(cfg)


@main.command()
@click.option("--config", "-c", default=None, help="Path to config file.")
@click.option("--severities", "-s", default=None, help="Comma-separated severities to show.")
@click.pass_context
def summary(ctx, config, severities):
    """Show a summary of SonarQube issues and distribution preview."""
    cfg = load_config(config or ctx.obj["config_path"])
    errors = cfg.validate()
    if errors:
        for err in errors:
            console.print(f"[red]Config error:[/] {err}")
        raise SystemExit(1)

    sev_list = severities.split(",") if severities else cfg.settings.severities

    console.print(f"\n[bold]Fetching issues from:[/] {cfg.sonarqube.host}")
    console.print(f"[bold]Project:[/] {cfg.sonarqube.project_key}\n")

    with SonarClient(
        host=cfg.sonarqube.host,
        token=cfg.sonarqube.token,
        project_key=cfg.sonarqube.project_key,
    ) as client:
        grouped = client.fetch_issues_grouped(severities=sev_list)

    total = sum(len(v) for v in grouped.values())
    console.print(f"[bold green]Total issues:[/] {total}\n")

    severity_table = Table(title="Issues by Severity")
    severity_table.add_column("Severity", style="bold")
    severity_table.add_column("Count", justify="right")

    for sev in sev_list:
        count = len(grouped.get(sev, []))
        if count > 0:
            severity_table.add_row(sev, str(count))

    console.print(severity_table)
    console.print()

    plan = distribute_issues(grouped, cfg.teammates, severities=sev_list)
    dist_table = Table(title="Distribution Preview")
    dist_table.add_column("Teammate", style="bold")
    for sev in sev_list:
        dist_table.add_column(sev, justify="right")
    dist_table.add_column("Total", justify="right", style="bold")

    summary_data = plan.summary()
    for teammate in cfg.teammates:
        row = [teammate.name]
        total_for_teammate = 0
        for sev in sev_list:
            count = summary_data.get(teammate.name, {}).get(sev, 0)
            total_for_teammate += count
            row.append(str(count) if count > 0 else "-")
        row.append(str(total_for_teammate))
        dist_table.add_row(*row)

    console.print(dist_table)
    console.print(f"\n[dim]Run 'sonar-jira-sync run' to open the web UI for approval.[/]\n")


@main.command()
@click.option("--config", "-c", default=None, help="Path to config file.")
@click.pass_context
def mcp(ctx, config):
    """Start the MCP server for AI assistant integration."""
    cfg_path = config or ctx.obj["config_path"]

    try:
        from .mcp.server import create_mcp_server
    except ImportError:
        console.print("[red]MCP support requires fastmcp.[/]")
        console.print("Install with: pip install sonar-jira-sync[mcp]")
        raise SystemExit(1)

    server = create_mcp_server(config_path=cfg_path)
    server.run()


if __name__ == "__main__":
    main()
