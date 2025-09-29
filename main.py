# Import the MCP server instance from server.py
from src.oracle_mcp_writer.server import mcp

if __name__ == "__main__":
    mcp.run(transport="sse")
