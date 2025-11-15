from fastmcp import FastMCP, Context

mcp = FastMCP("Demo 🚀")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool
def hello(ctx: Context = None):
    """Say hello"""
    if ctx:
        ctx.info("in Hello!")
    return {"Response": "Hello!"}

@mcp.resource("config://version")
def get_version(ctx: Context):
    ctx.info("Sono in get_version!")
    return "2.0.1"

if __name__ == "__main__":
    mcp.run(
        transport='http',
        host="0.0.0.0",
        port=8888
        )
