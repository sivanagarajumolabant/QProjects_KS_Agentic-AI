import asyncio, json
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    print('MCP Client Started')
    server_script_path = "C:/QProjects/MCP_Samples/sample/setup_db_server.py"  # correct absolute path!

    server_params = StdioServerParameters(
        command="python",
        args=[server_script_path],
        env=None
    )

    async with AsyncExitStack() as stack:
        stdio_transport = await stack.enter_async_context(stdio_client(server_params))
        session = await stack.enter_async_context(ClientSession(*stdio_transport))

        await session.initialize()
        result = await session.call_tool("get_user_info", {"user_id": 2})

        # Correctly handle MCP content response
        content_item = result.content[0]
        if hasattr(content_item, 'data'):
            print(json.dumps(content_item.data, indent=4))
        elif hasattr(content_item, 'text'):
            print(content_item.text)
        else:
            print(str(content_item))

asyncio.run(main())