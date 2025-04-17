from mcp.server.fastmcp import FastMCP
import sqlite3

mcp = FastMCP("sqlite-db-server")

@mcp.tool()
async def get_user_info(user_id: int) -> dict:
    """Get user info by ID."""
    conn = sqlite3.connect("C:/QProjects/MCP_Samples/sample/users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id,name,email FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return {"id":user[0],"name":user[1],"email":user[2]}
    else:
        return {"error":"No user found"}

if __name__ == "__main__":
    print('MCP Server Started')
    mcp.run(transport='stdio')
