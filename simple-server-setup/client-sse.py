import os
import asyncio
from google import genai
from typing import Optional
from dotenv import load_dotenv
from contextlib import AsyncExitStack
from mcp.client.sse import sse_client
from mcp import ClientSession

load_dotenv()

"""
Make sure:
1. The server is running before running this script.
2. The server is configured to use SSE transport.
3. The server is listening on port 8050.

To run the server:
uv run server.py
"""

class CalculatorMCPClient:
    def __init__(self, api_key: str):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.gemini = genai.Client(
            api_key=api_key
        )
    
    async def connect_to_server(self, server_endpoint: str = "http://localhost:8050"):
        """Connect to the MCP Server via SSE
        """
        print(f"Connecting to MCP Server at {server_endpoint}...")
        server_endpoint = server_endpoint + "/sse"
        # Connect to the server
        sse_transport = await self.exit_stack.enter_async_context(sse_client(server_endpoint))
        self.read_stream, self.write_stream = sse_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.read_stream, self.write_stream))
    
        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using Gemini and available tools"""
        pass

    async def simple_call_to_mcp(self):
        """Simple call to the MCP Server"""
        try:
            result = await self.session.call_tool("add", arguments={"a": 2, "b": 3})
            print("Response from MCP Server:", result)
        except Exception as e:
            print("Error calling MCP Server:", str(e))

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = CalculatorMCPClient(api_key)

    try: 
        await client.connect_to_server()
        await client.simple_call_to_mcp()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
