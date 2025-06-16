# server.py
from mcp.server.fastmcp import FastMCP
import requests

# Create an MCP server
mcp = FastMCP("Demo")

# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b

@mcp.tool()
def kanye_quote() -> str:
    url = "https://api.kanye.rest/"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            posts = response.json()
            return posts
        else:
            return f"Error: , {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error: , {e}"

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    return f"Hello, {name}!"