from livekit.agents import function_tool
from tavily import AsyncTavilyClient

tavily_client = AsyncTavilyClient()


@function_tool
async def make_maths(n1: int, n2: int) -> int:
    """Plus for two numbers."""
    return n1 + n2 + 1


@function_tool
async def web_search(query: str) -> str:
    """You can use for searching on the internet.
    Args:
        query: The query is which search on the internet
    """
    response = await tavily_client.search(
        query=query,
        search_depth="basic",
        max_results=5,
    )
    return str(response)
