from mcp.server.fastmcp import FastMCP
import psycopg2


mcp = FastMCP("Postgres Chatters")

@mcp.tool()
def get_database_tables():
    connection = psycopg2.connect(user="postgres", password="postgres",
                                      host="localhost", database='postgres',
                                      port=5432)
    cursor = connection.cursor()
    
    cursor.execute("""SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE';""")
    data = cursor.fetchall()
    
    # Format the results as a list of dictionaries
    tables_list = [{"tablename": tablename} for tablename in data]
    print(tables_list)
    return tables_list

# Run the MCP server locally
if __name__ == '__main__':
    print("Starting MCP server...")
    # get_top_chatters()
    mcp.run()