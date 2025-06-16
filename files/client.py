# stdio is the protocol meant things to run on your local machine
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import json


# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="mcp", # Executable
    args=["run","server.py"], # Optional command line arguments
    env=None # Optional environment variables
)

functions = []

# Converts MCP tool response into a format LLM can understand
def convert_to_llm_tool(tool):
    tool_schema = {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "type": "function",
            "parameters": {
                "type":"object",
                "properties": tool.inputSchema["properties"]
            }
        }
    }

    return tool_schema

# Passing functions from MCP server to LLM
def call_llm(prompt,functions):
    token = os.environ["GITHUB_TOKEN"]
    endpoint = "https://models.inference.ai.azure.com"

    model_name = "gpt-4o"

    client = ChatCompletionsClient(
        endpoint = endpoint,
        credential = AzureKeyCredential(token)
    )

    print("Calling LLM")
    response = client.complete(
        messages = [
            {
                "role":"system",
                "content": "You are a helpful assistant"
            },
            {
                "role":"user",
                "content": prompt
            },
        ],
        model = model_name,
        # Passing functions as tools LLM can use
        tools = functions,
        # Optional parameters
        temperature=1,
        max_tokens=1000,
        top_p=1.
    )


    response_message = response.choices[0].message

    functions_to_call = []

    # Inspecting result to see what functions we should call, if any
    # If response_message.tool_calls exists- i.e. whether LLM decided to invoke any function(s)
    if response_message.tool_calls:
        print()
        print("Tools LLM requested: ")
        for tool_call in response_message.tool_calls:
            print("Tool: ", tool_call)
            name = tool_call.function.name
            # Passing args into python Dict
            args = json.loads(tool_call.function.arguments)
            functions_to_call.append({"name": name, "args": args})
    
    # returning array of functions to be called
    return functions_to_call

async def run():
    async with stdio_client(server_params) as (read,write):
        async with ClientSession(read,write) as session:
            #Initialize the connection
            await session.initialize()

            # Listing available resources
            resources = await session.list_resources()
            print("Listing RESORUCES")
            for resource in resources:
                print("Resource: ", resource)
            

            # Listing available tools
            tools = await session.list_tools()
            print("Listing TOOLS")
            for tool in tools.tools:
                print("Tool: ", tool.name)
                print("Tool ", tool.inputSchema["properties"])
                
                functions.append(convert_to_llm_tool(tool))


            prompt = input("enter prompt: ")

            # Ask LLM what tools to call, if any
            functions_to_call = call_llm(prompt,functions)

            # Calling suggested functions
            for f in functions_to_call:
                result = await session.call_tool(f["name"], arguments=f["args"])
                print("TOOLS result: ", result.content)





if __name__ == "__main__":
    import asyncio
    
    asyncio.run(run())
