import os
import asyncio
from google import genai
from typing import Optional
from dotenv import load_dotenv
from contextlib import AsyncExitStack
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

load_dotenv()


class CalculatorMCPClient:
    def __init__(self, api_key: str):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.gemini = genai.Client(
            api_key=api_key
        )
    async def connect_to_server(self, server_script_path: str = None):
        """Connect to the MCP Server
        
        Args: 
            server_script_path: Path to the server script (.py or .js), only in case of stdio
        """
        # Define server parameters
        server_params = StdioServerParameters(
            command="python",  # The command to run your server
            args=["server.py", "--transport", "stdio"],  # Arguments to the command
        )
        print("Starting the MCP Server...")

        # Connect to the server
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.read_stream, self.write_stream = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.read_stream, self.write_stream))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Prcess a query using Gemini and available tools"""
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
        await client.cleanup() # close the connection with server and stops the server, also performs cleanup

if __name__ == "__main__":
    asyncio.run(main())