import asyncio

from livekit.agents import function_tool, RunContext
from tavily import AsyncTavilyClient


tavily_client = AsyncTavilyClient()


async def speak_tool_ack(
    context: RunContext,
) -> None:
    await context.session.generate_reply(
        instructions="""
        Kullanıcıya çok kısa ve doğal bir şekilde,
        istediği bilgiyi şu anda kontrol ettiğini söyle.

        Sonucu henüz söyleme.
        Herhangi bir bilgi uydurma.
        En fazla tek kısa cümle kullan.
        Aynı ifadeyi sürekli tekrar etme.
        """
    )


async def delayed_ack(
    context: RunContext,
    delay: float = 0.5,
) -> None:
    await asyncio.sleep(delay)
    await speak_tool_ack(context)


@function_tool
async def make_maths(
    n1: int,
    n2: int,
) -> int:
    """Add two numbers."""
    return n1 + n2


@function_tool
async def web_search(
    context: RunContext,
    query: str,
) -> str:
    """
    Search the internet for current information.

    Args:
        query: Search query.
    """

    ack_task = asyncio.create_task(
        delayed_ack(context)
    )

    try:
        response = await tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=5,
        )

        return str(response)

    finally:
        # Yalnızca acknowledgement henüz başlamadıysa
        # iptal etmeyi hedefliyoruz.
        if not ack_task.done():
            ack_task.cancel()

            try:
                await ack_task
            except asyncio.CancelledError:
                pass