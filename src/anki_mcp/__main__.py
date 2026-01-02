"""Entry point for the Anki MCP server."""

import asyncio
import sys

from rich.console import Console

from anki_mcp.server import create_server, lifespan


console = Console()


def main() -> None:
    """Run the Anki MCP server."""
    try:
        # Create and configure the server
        mcp = create_server()

        # Run the server with stdio transport
        mcp.run()

    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error starting server: {e}[/red]")
        sys.exit(1)


async def check_connection() -> bool:
    """Check if AnkiConnect is available."""
    from anki_mcp.client.base import AnkiConnectClient
    from anki_mcp.config import get_settings

    settings = get_settings()
    client = AnkiConnectClient(settings)

    try:
        connected = await client.is_connected()
        if connected:
            console.print("[green]AnkiConnect is available[/green]")
        else:
            console.print("[red]AnkiConnect is not responding[/red]")
        return connected
    finally:
        await client.close()


if __name__ == "__main__":
    # Check for special commands
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check":
            # Check AnkiConnect connection
            asyncio.run(check_connection())
        elif sys.argv[1] == "--version":
            from anki_mcp import __version__
            console.print(f"anki-mcp version {__version__}")
        elif sys.argv[1] == "--help":
            console.print("[bold]Anki MCP Server[/bold]")
            console.print()
            console.print("Usage: python -m anki_mcp [OPTIONS]")
            console.print()
            console.print("Options:")
            console.print("  --check    Check AnkiConnect connection")
            console.print("  --version  Show version")
            console.print("  --help     Show this help message")
            console.print()
            console.print("Environment variables:")
            console.print("  ANKI_MCP_HOST     AnkiConnect host (default: localhost)")
            console.print("  ANKI_MCP_PORT     AnkiConnect port (default: 8765)")
            console.print("  ANKI_MCP_API_KEY  AnkiConnect API key (optional)")
            console.print("  ANKI_MCP_TIMEOUT  HTTP timeout in seconds (default: 30)")
            console.print("  ANKI_MCP_DEBUG    Enable debug mode (default: false)")
        else:
            console.print(f"[red]Unknown option: {sys.argv[1]}[/red]")
            sys.exit(1)
    else:
        main()
