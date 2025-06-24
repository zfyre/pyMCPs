import os
import asyncio
from typing import Optional
from contextlib import AsyncExitStack
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from google import genai
from google.genai import types
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self, api_key: str):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.gemini = genai.Client(
            api_key=api_key
        )
    # methods will go here
    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from MCP server"""
        tools_result = await self.session.list_tools()
        return [ # Return tools in Gemini tool format
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            }
            for tool in tools_result.tools
        ]
    
    async def process_query(self, query: str) -> str:
        """Process a query using Gemini and available tools"""
        # Get available tools from MCP server
        tools_data = await self.get_tools() # Since Gemini uses OpenAI tool format, hence it'll work
        tools = types.Tool(function_declarations=tools_data)
        config = types.GenerateContentConfig(
            system_instruction="You are an efficient calculator. You can only use the tools provided to you to answer the user's question.",
            tools=[tools],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
            # Force the model to call 'any' function, instead of chatting.
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode='AUTO')
            ),
        )
        # Define user prompt
        contents = [
            types.Content(
                role="user", parts=[types.Part(text=query)]
            )
        ]

        # Send request with function declarations
        response = self.gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config,
        )
        
        while response.function_calls:
            for fn in response.function_calls:  
                print("Calling tool: ", fn.name)
                result = await self.session.call_tool(
                    fn.name,
                    arguments=fn.args
                )
                print("Result: ", result)
                # Create a function response part
                function_response_part = types.Part.from_function_response(
                    name=fn.name,
                    response={"result": result},
                )
                # Append function call and result of the function execution to contents
                contents.append(response.candidates[0].content) # Append the content from the model's response.
                contents.append(types.Content(role="user", parts=[function_response_part])) # Append the function response
        
            response = self.gemini.models.generate_content(
                model="gemini-2.5-flash",
                config=config,
                contents=contents,
            )
        
        final_response = self.gemini.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction="You are a cat. Your name is Neko."),
            contents=contents,
        )
        
        return final_response.text

        
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()
        
async def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = MCPClient(api_key)

    try: 
        await client.connect_to_server("servers/simple_server.py")
        result = await client.process_query("What is (5 + 3)*8?")
        print(result)
    except Exception as e:
        print(e)
    finally:
        await client.cleanup() # close the connection with server and stops the server, also performs cleanup

if __name__ == "__main__":
    asyncio.run(main()) 