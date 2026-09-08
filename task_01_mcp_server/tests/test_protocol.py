import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError
from mcp.types import INVALID_PARAMS, METHOD_NOT_FOUND

SERVER_PARAMS = StdioServerParameters(command=sys.executable, args=["-m", "app.server"])


@pytest.mark.asyncio
async def test_invalid_customer_id_returns_invalid_params():
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            with pytest.raises(McpError) as exc_info:
                await session.call_tool("get_customer_record", {"customer_id": "bad-id"})
            assert exc_info.value.error.code == INVALID_PARAMS


@pytest.mark.asyncio
async def test_invalid_refund_returns_invalid_params():
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            with pytest.raises(McpError) as exc_info:
                await session.call_tool(
                    "trigger_refund",
                    {"customer_id": "CUST-12345", "amount": 0, "reason": "short"},
                )
            assert exc_info.value.error.code == INVALID_PARAMS


@pytest.mark.asyncio
async def test_unknown_tool_returns_method_not_found():
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            with pytest.raises(McpError) as exc_info:
                await session.call_tool("admin_delete_everything", {})
            assert exc_info.value.error.code == METHOD_NOT_FOUND


@pytest.mark.asyncio
async def test_valid_calls_succeed():
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_customer_record", {"customer_id": "CUST-12345"})
            assert result.isError is False

            result = await session.call_tool(
                "trigger_refund",
                {"customer_id": "CUST-12345", "amount": 25.5, "reason": "Customer requested refund"},
            )
            assert result.isError is False
