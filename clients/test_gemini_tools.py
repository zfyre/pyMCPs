import asyncio
import os
from simple_client import MCPClient
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Check if API key is available
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Please set your Gemini API key in the .env file")
        return

    # Initialize the client
    client = MCPClient()
    
    try:
        # Connect to the MCP server
        server_path = "servers/simple_server.py"
        print(f"Connecting to MCP server at: {server_path}")
        await client.connect_to_server(server_path)
        
        # Test queries that should trigger tool calls
        test_queries = [
            "What is 5 + 3?",
            "Can you add 10 and 20 for me?",
            "I need to calculate 15 + 25",
            "What's the sum of 7 and 9?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*50}")
            print(f"Test {i}: {query}")
            print(f"{'='*50}")
            
            try:
                result = await client.process_query(query)
                print(f"Result:\n{result}")
            except Exception as e:
                print(f"Error processing query: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"Error during setup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        print("\nCleaning up...")
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 