"""MCP Tools for Anki media operations."""

import base64
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from anki_mcp.client.base import AnkiConnectError
from anki_mcp.server import get_anki_actions


def register_media_tools(mcp: FastMCP) -> None:
    """Register media-related tools with the MCP server.

    Tools:
    - store_media: Store a media file in Anki
    - get_media: Retrieve a media file from Anki
    - delete_media: Delete a media file
    - list_media: List media files
    """

    @mcp.tool()
    async def store_media(
        filename: str,
        data: str | None = None,
        file_path: str | None = None,
        url: str | None = None,
    ) -> dict:
        """Store a media file in Anki's media folder.

        Provide ONE of: data, file_path, or url.

        Args:
            filename: Target filename in Anki's media folder.
            data: Base64-encoded file content.
            file_path: Path to a local file.
            url: URL to download the file from.

        Returns:
            The stored filename.

        Example:
            store_media(
                filename="pronunciation.mp3",
                url="https://example.com/audio.mp3"
            )
        """
        try:
            actions = get_anki_actions()

            if sum(x is not None for x in [data, file_path, url]) != 1:
                return {"error": "Provide exactly one of: data, file_path, or url"}

            # If file_path provided, read and encode
            if file_path:
                path = Path(file_path)
                if not path.exists():
                    return {"error": f"File not found: {file_path}"}
                data = base64.b64encode(path.read_bytes()).decode()

            stored_name = await actions.store_media_file(
                filename=filename,
                data=data,
                url=url,
            )

            return {
                "success": True,
                "filename": stored_name,
                "message": f"Media file '{stored_name}' stored successfully",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_media(filename: str) -> dict:
        """Retrieve a media file from Anki.

        Args:
            filename: The filename to retrieve.

        Returns:
            Base64-encoded file content.
        """
        try:
            actions = get_anki_actions()
            data = await actions.retrieve_media_file(filename)

            if not data:
                return {"error": f"Media file '{filename}' not found"}

            return {
                "filename": filename,
                "data": data,
                "encoding": "base64",
                "size_bytes": len(base64.b64decode(data)),
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def delete_media(filename: str) -> dict:
        """Delete a media file from Anki.

        Args:
            filename: The filename to delete.

        Returns:
            Confirmation of deletion.
        """
        try:
            actions = get_anki_actions()
            await actions.delete_media_file(filename)

            return {
                "success": True,
                "filename": filename,
                "message": f"Media file '{filename}' deleted",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def list_media(pattern: str = "*") -> dict:
        """List media files in Anki's media folder.

        Args:
            pattern: Glob pattern to match (default: "*" for all files).
                    Examples: "*.mp3", "image_*", "*.jpg"

        Returns:
            List of matching filenames.
        """
        try:
            actions = get_anki_actions()
            files = await actions.get_media_files_names(pattern)

            # Group by extension
            by_extension: dict[str, list[str]] = {}
            for f in files:
                ext = Path(f).suffix.lower() or "no_extension"
                if ext not in by_extension:
                    by_extension[ext] = []
                by_extension[ext].append(f)

            return {
                "files": files,
                "total": len(files),
                "by_extension": {k: len(v) for k, v in sorted(by_extension.items())},
                "pattern": pattern,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}
