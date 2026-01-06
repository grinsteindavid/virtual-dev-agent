#!/usr/bin/env python3
"""CLI entry point for running virtual developer tasks."""

import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.logger import get_logger
from src.agents.graph import create_dev_workflow

logger = get_logger(__name__)


def main():
    """Run the virtual developer workflow for a Jira ticket."""
    parser = argparse.ArgumentParser(
        description="Virtual Developer Agent - Automate Jira ticket to PR workflow"
    )
    parser.add_argument(
        "--ticket",
        "-t",
        default=None,
        help="Jira ticket ID (e.g., DP-123). Falls back to TICKET env var.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no actual changes)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    ticket = args.ticket or config.workflow.ticket
    if not ticket:
        logger.error("No ticket specified. Use --ticket or set TICKET env var.")
        sys.exit(1)
    
    errors = config.validate()
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    logger.info(f"Starting workflow for ticket: {ticket}")
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    
    try:
        graph = create_dev_workflow()
        
        initial_state = {
            "jira_ticket_id": ticket,
            "status": "pending",
        }
        
        thread_id = str(uuid.uuid4())
        config_dict = {"configurable": {"thread_id": thread_id}}
        logger.info(f"Thread ID: {thread_id}")
        
        result = graph.invoke(initial_state, config=config_dict)
        
        logger.info("=" * 50)
        logger.info("WORKFLOW COMPLETE")
        logger.info("=" * 50)
        logger.info(f"Status: {result.get('status', 'unknown')}")
        logger.info(f"PR URL: {result.get('pr_url', 'N/A')}")
        logger.info(f"Test Results: {result.get('test_results', {})}")
        
        if result.get("error"):
            logger.error(f"Error: {result['error']}")
            sys.exit(1)
        
        if result.get("status") == "done":
            logger.info("✅ Workflow completed successfully!")
            sys.exit(0)
        else:
            logger.warning(f"⚠️ Workflow ended with status: {result.get('status')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Workflow interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
