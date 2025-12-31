"""
ActProof.ai - Command Line Interface
Main CLI for ActProof.ai Repository Intelligence Scanner
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from actproof.scanner.repository_scanner import RepositoryScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def setup_argparse() -> argparse.ArgumentParser:
    """
    Configure command-line argument parser

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="ActProof.ai - Repository Intelligence Scanner for EU AI Act Compliance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s scan ./my-ai-project
  %(prog)s scan ./my-ai-project --output ./compliance/ai-bom.json
  %(prog)s scan ./my-ai-project --format yaml --creator "My Company"
        """
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands"
    )

    # Scan command
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a repository for AI/ML components"
    )
    scan_parser.add_argument(
        "path",
        type=str,
        help="Path to the repository directory"
    )
    scan_parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output path for AI-BOM document (default: auto-generated)"
    )
    scan_parser.add_argument(
        "--format", "-f",
        choices=["json", "yaml"],
        default="json",
        help="Output format for AI-BOM (default: json)"
    )
    scan_parser.add_argument(
        "--creator", "-c",
        type=str,
        default="ActProof.ai Scanner",
        help="Creator name for the AI-BOM document"
    )
    scan_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging output"
    )

    return parser


def handle_scan_command(args: argparse.Namespace) -> int:
    """
    Handle the 'scan' command

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Validate repository path
    repo_path = Path(args.path).resolve()
    if not repo_path.exists():
        logger.error(f"Repository path not found: {repo_path}")
        return 1

    if not repo_path.is_dir():
        logger.error(f"Path is not a directory: {repo_path}")
        return 1

    try:
        logger.info(f"Scanning repository: {repo_path}")
        scanner = RepositoryScanner(repo_path)

        # Execute scan
        logger.info("Starting AI component detection...")
        results = scanner.scan()

        # Display summary
        logger.info("\n" + "=" * 60)
        logger.info("Scan Results Summary")
        logger.info("=" * 60)
        logger.info(f"Repository: {results['repository_path']}")
        logger.info(f"Git Repository: {results['is_git_repository']}")
        logger.info(f"\nComponents Detected:")
        logger.info(f"  - AI Models: {results['summary']['models_found']}")
        logger.info(f"  - Datasets: {results['summary']['datasets_found']}")
        logger.info(f"  - Dependencies: {results['summary']['dependencies_found']}")

        # Generate AI-BOM
        output_path_arg: Optional[Path] = Path(args.output) if args.output else None
        logger.info(f"\nGenerating AI-BOM ({args.format} format)...")

        output_path = scanner.generate_bom(
            output_path=output_path_arg,
            format=args.format,
            creator=args.creator
        )

        logger.info(f"AI-BOM successfully generated: {output_path}")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Error during repository scan: {e}", exc_info=args.verbose)
        return 1


def main() -> int:
    """
    Main entry point for CLI

    Returns:
        Exit code
    """
    parser = setup_argparse()
    args = parser.parse_args()

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 1

    # Route to command handler
    if args.command == "scan":
        return handle_scan_command(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
