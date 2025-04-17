from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hello-world")

@mcp.tool()
async def say_hello(name: str) -> str:
    """Say Hello to a person.

    Args:
        name: The person's name.
    """
    return f"Hello, {name}! 🎉"

if __name__ == "__main__":
    print('MCP Server Started')
    mcp.run(transport='stdio')