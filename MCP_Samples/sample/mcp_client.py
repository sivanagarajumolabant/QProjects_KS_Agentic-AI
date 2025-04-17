import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    print('MCP Client Started')
    server_script_path = "C:\QProjects\MCP_Samples\sample\mcp_server.py"  # correct absolute path!

    server_params = StdioServerParameters(
        command="python",
        args=[server_script_path],
        env=None
    )

    async with AsyncExitStack() as stack:
        stdio_transport = await stack.enter_async_context(stdio_client(server_params))
        session = await stack.enter_async_context(ClientSession(*stdio_transport))

        await session.initialize()
        result = await session.call_tool("say_hello", {"name": "MCP User"})
        
        # Correctly handle MCP response
        content_item = result.content[0]
        print(content_item.text)

asyncio.run(main())