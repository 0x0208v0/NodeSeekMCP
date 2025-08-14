import asyncio

from fastmcp import Client

client = Client("http://localhost:8866/mcp/nodeseek")


async def main():
    async with client:
        await client.ping()

        tools = await client.list_tools()
        print(tools)

        resources = await client.list_resources()
        prompts = await client.list_prompts()

        result = await client.call_tool("get_nodeseek_bbs_or_ns_bbs_rss_feed_post_history", {"page_size": "2"})
        print(result)


if __name__ == '__main__':
    asyncio.run(main())
