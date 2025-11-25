"""
Web Search Tool - Search the internet using DuckDuckGo
"""

import requests
from bs4 import BeautifulSoup
import os

# Fix fake_useragent issue in PyInstaller builds
# Set fallback User-Agent before importing DDGS
os.environ["FAKE_USERAGENT_FALLBACK"] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Monkey-patch fake_useragent to avoid file loading issues
try:
    import fake_useragent

    # Override the UserAgent class to always return our fallback
    class StaticUserAgent:
        def __getattr__(self, name):
            return os.environ.get("FAKE_USERAGENT_FALLBACK", "Mozilla/5.0")

    fake_useragent.UserAgent = StaticUserAgent
except ImportError:
    pass

try:
    from ddgs import DDGS  # New package name
except ImportError:
    from duckduckgo_search import DDGS  # Fallback for legacy installations
from .base import Tool


class WebSearchTool(Tool):
    """Search the internet for information using DuckDuckGo"""

    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the internet for information using DuckDuckGo",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 3)",
                        "default": 3,
                    },
                    "fetch_content": {
                        "type": "boolean",
                        "description": "Whether to fetch full page content (default: true)",
                        "default": True,
                    },
                },
                "required": ["query"],
            },
        )

    def _fetch_page_content(self, url: str, max_chars: int = 3000) -> str:
        """
        Fetch and extract text content from a webpage

        Args:
            url: The URL to fetch
            max_chars: Maximum characters to return

        Returns:
            Extracted text content or error message
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text content
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            # Truncate if too long
            if len(text) > max_chars:
                text = text[:max_chars] + "..."

            return text

        except requests.Timeout:
            return "[Timeout: Page took too long to load]"
        except requests.RequestException as e:
            return f"[Error fetching page: {str(e)[:100]}]"
        except Exception as e:
            return f"[Error parsing page: {str(e)[:100]}]"

    def execute(
        self, query: str, max_results: int = 3, fetch_content: bool = True
    ) -> str:
        """Search the web using DuckDuckGo"""
        from http.client import HTTPException

        try:
            with DDGS() as ddgs:
                # Perform web search
                try:
                    results = list(ddgs.text(query, max_results=max_results))
                except (KeyError, AttributeError, TypeError) as e:
                    # API might have changed, try alternative method
                    return f"Web search temporarily unavailable (API error: {str(e)}). Please try again later or rephrase your query."
                except Exception as e:
                    return f"Web search error: {type(e).__name__}: {str(e)}"

            if not results:
                return "No results found."

            # Create a clear header to indicate this is actual content, not just links
            formatted_results = [
                "WEB SEARCH RESULTS - Full content extracted and ready to use:\n"
            ]

            for i, result in enumerate(results, 1):
                # Safely extract fields (API format may vary)
                title = result.get("title", "No title")
                url = result.get("href", result.get("url", "No URL"))
                snippet = result.get(
                    "body",
                    result.get("snippet", result.get("description", "No description")),
                )

                formatted_results.append(f"\n{'=' * 80}")
                formatted_results.append(f"Result #{i}: {title}")
                formatted_results.append(f"{'=' * 80}")

                if fetch_content:
                    # Fetch full page content
                    formatted_results.append(
                        f"\n[Fetching full content from {url}...]\n"
                    )
                    full_content = self._fetch_page_content(url)
                    formatted_results.append(f"FULL PAGE CONTENT:\n{full_content}\n")
                else:
                    # Use snippet only
                    formatted_results.append(f"\nSNIPPET: {snippet}\n")

                formatted_results.append(f"Source URL: {url}")

            formatted_results.append(f"\n{'=' * 80}")
            formatted_results.append(
                f"\nNOTE: The content above has been extracted from actual web pages. "
                f"You can directly use and cite this information in your response. "
                f"You do NOT need to visit the URLs - the full content is already provided above."
            )

            return "\n".join(formatted_results)
        except HTTPException as e:
            return f"Error performing web search: {str(e)}"
