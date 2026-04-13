"""Analyst A2A server — exposes the analyst agent via Agent-to-Agent protocol."""

import uvicorn
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from analyst_agent.agent import root_agent

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="finops_analyst",
    session_service=session_service,
)


def main():
    """Run the analyst agent as a standalone A2A service on port 8001."""
    from google.adk.cli import cli

    # Use ADK's built-in web server for the analyst agent
    # This exposes both the ADK dev UI and the A2A endpoint
    cli.main(["web", "--port", "8001", "--agent_dir", "analyst_agent"])


if __name__ == "__main__":
    main()
