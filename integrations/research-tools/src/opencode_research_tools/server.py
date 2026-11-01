"""Explicitly started stdio bridge. No network listener or startup API calls."""
from .zotero import Zotero, better_bibtex


def build_server():
    from mcp.server.fastmcp import FastMCP
    app = FastMCP('OpenCode Zotero')

    @app.tool()
    def status() -> dict:
        """Check the selected Zotero API's availability and local write capability."""
        return Zotero().status()

    @app.tool()
    def search(query: str, limit: int = 20, start: int = 0) -> dict:
        """Search library metadata. This does not upload documents or change Zotero."""
        return Zotero().search(query, limit, start)

    @app.tool()
    def item(key: str) -> dict:
        """Read one Zotero item by its eight-character key."""
        return Zotero().get(key)

    @app.tool()
    def collections(limit: int = 50, start: int = 0) -> dict:
        """List a bounded page of collections."""
        return Zotero().collections(limit, start)

    @app.tool()
    def collection_items(key: str, limit: int = 50, start: int = 0) -> dict:
        """Read a bounded page of items in a collection."""
        return Zotero().collection_items(key, limit, start)

    @app.tool()
    def tags(limit: int = 50, start: int = 0) -> dict:
        """List a bounded page of tags."""
        return Zotero().tags(limit, start)

    @app.tool()
    def attachments(key: str) -> dict:
        """List item children including attachment metadata; does not open local files."""
        return Zotero().children(key)

    @app.tool()
    def fulltext(attachment_key: str) -> dict:
        """Read indexed attachment text. Page numbers are not guaranteed."""
        return Zotero().fulltext(attachment_key)

    @app.tool()
    def export(keys: list[str], format: str = 'bibtex') -> dict:
        """Return selected references as BibTeX, BibLaTeX, RIS or CSL JSON without writing a file."""
        return Zotero().export(keys, format)

    @app.tool()
    def bbt_ready() -> dict:
        """Check whether the optional Better BibTeX API is available locally."""
        return better_bibtex('api.ready')

    @app.tool()
    def citation_keys(keys: list[str]) -> dict:
        """Resolve Better BibTeX citation keys for selected Zotero item keys."""
        from .zotero import item_key
        return better_bibtex('item.citationkey', [[item_key(k) for k in keys]])

    @app.tool()
    def bbt_export(citekeys: list[str], translator: str = 'Better BibTeX') -> str:
        """Export selected Better BibTeX citekeys without changing the library."""
        return better_bibtex('item.export', [citekeys, translator])

    @app.tool()
    def import_preview(items: list[dict]) -> dict:
        """Preview an import and its digest. No network calls or library writes."""
        return Zotero().preview_import(items)

    @app.tool()
    def import_items(items: list[dict], confirm_digest: str) -> dict:
        """WRITE: explicitly approved import only. Requires reviewed digest; checks existing DOIs. Local writes show Zotero's authorization dialog."""
        return Zotero().import_items(items, confirm_digest)

    return app
