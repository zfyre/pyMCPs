import os
import argparse
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Create an MCP Server
mcp = FastMCP(
    name="Calculator",
    host="0.0.0.0", # only needed when using SSE transport
    port=8050 # only needed when using SSE transport
)

# Add a simple calculator tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers together"""
    return a * b



# Run the server
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the MCP Server")
    parser.add_argument("--transport", type=str, default="stdio", choices=["stdio", "sse"], help="Transport mode (stdio or sse)")
    args = parser.parse_args()

    transport = args.transport
    if transport == "stdio":
        print("Running in stdio mode")
        mcp.run(transport="stdio")
    elif transport == "sse": # Define the host and port for SSE transport
        print("Running in SSE mode")
        mcp.run(transport="sse")
    else:
        raise ValueError(f"Invalid transport: {transport}")