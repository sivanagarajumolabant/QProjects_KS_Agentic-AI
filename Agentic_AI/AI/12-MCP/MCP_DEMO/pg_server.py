from mcp.server.fastmcp import FastMCP
import psycopg2

mcp = FastMCP("Postgres Server")

@mcp.tool()
def get_database_tables():
    connection = psycopg2.connect(user="postgres", password="postgres",
                                      host="localhost", database='postgres',
                                      port=5432)
    cursor = connection.cursor()
    
    cursor.execute("""SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema NOT IN ('pg_catalog', 'information_schema');""")
    data = cursor.fetchall()
    
    # Format the results as a list of dictionaries
    tables_list = [{"tablename": tablename} for tablename in data]
    print(tables_list)
    return tables_list