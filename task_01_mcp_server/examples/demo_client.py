"""Example client for the Task 1 MCP server. Spawns app.server over stdio and
exercises both tools, valid and invalid, printing the JSON-RPC results.

Not part of the graded deliverable - tests/test_protocol.py already covers this
programmatically. This is just a convenience script for interactive exploration.

Run from the task_01_mcp_server directory (not from examples/) with the venv
activated, so `app.server` resolves as a module:
    python examples\\demo_client.py
"""
import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError

SERVER_PARAMS = StdioServerParameters(command=sys.executable, args=["-m", "app.server"])


async def try_call(session, name, arguments):
    print(f"\n--- {name}({arguments}) ---")
    try:
        result = await session.call_tool(name, arguments)
        print("isError:", result.isError)
        for block in result.content:
            print("content:", block.text if hasattr(block, "text") else block)
    except McpError as e:
        print(f"JSON-RPC error {e.error.code}: {e.error.message}")
        if e.error.data:
            print("data:", e.error.data)


async def main():
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Registered tools:")
            for t in tools.tools:
                print(f"  {t.name}: {t.inputSchema}")

            # Valid calls
            await try_call(session, "get_customer_record", {"customer_id": "CUST-12345"})
            await try_call(session, "trigger_refund", {
                "customer_id": "CUST-12345", "amount": 25.5, "reason": "Customer requested refund",
            })

            # Invalid calls -> should surface real JSON-RPC error codes, not isError:true
            await try_call(session, "get_customer_record", {"customer_id": "not-a-valid-id"})
            await try_call(session, "trigger_refund", {
                "customer_id": "CUST-12345", "amount": 0, "reason": "short",
            })
            await try_call(session, "nonexistent_tool", {})


if __name__ == "__main__":
    asyncio.run(main())
