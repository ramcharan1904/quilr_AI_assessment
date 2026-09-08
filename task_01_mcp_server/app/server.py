import logging
import sys

from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import INVALID_PARAMS, METHOD_NOT_FOUND, CallToolRequest, ErrorData
from pydantic import ValidationError

from .schemas import CustomerId, RefundAmount, RefundReason
from .tools import get_customer_record as _get_customer_record_impl
from .tools import trigger_refund as _trigger_refund_impl

logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                    format="%(asctime)s %(levelname)s %(message)s")

mcp = FastMCP("FDE Customer Server")

@mcp.tool()
def get_customer_record(customer_id: CustomerId) -> dict:
    return _get_customer_record_impl(customer_id)

@mcp.tool()
def trigger_refund(customer_id: CustomerId, amount: RefundAmount, reason: RefundReason) -> dict:
    return _trigger_refund_impl(customer_id, amount, reason)

# FastMCP's own tool dispatch (registered above via `Server.call_tool()`) catches every
# exception except `UrlElicitationRequiredError` and folds it into a "successful"
# CallToolResult(isError=True) - there is no way to make a *validated* tool raise a real
# top-level JSON-RPC error from inside that path. To satisfy "reject invalid formats with
# standard MCP JSON-RPC error codes", we install our own CallToolRequest handler that runs
# validation *before* handing off to FastMCP's handler, and raises McpError directly - that
# exception is caught by the SDK's request dispatcher (mcp.server.lowlevel.server.Server.
# _handle_request) and surfaces as a genuine JSON-RPC `error` object, not a tool result.
_TOOL_SCHEMAS = {
    "get_customer_record": mcp._tool_manager.get_tool("get_customer_record").parameters,
    "trigger_refund": mcp._tool_manager.get_tool("trigger_refund").parameters,
}
_default_call_tool_handler = mcp._mcp_server.request_handlers[CallToolRequest]

async def _validating_call_tool_handler(req: CallToolRequest):
    name = req.params.name
    if name not in _TOOL_SCHEMAS:
        raise McpError(ErrorData(code=METHOD_NOT_FOUND, message=f"Unknown tool: {name}"))

    tool = mcp._tool_manager.get_tool(name)
    arguments = req.params.arguments or {}
    try:
        tool.fn_metadata.arg_model(**arguments)
    except ValidationError as e:
        raise McpError(ErrorData(
            code=INVALID_PARAMS,
            message=f"Invalid parameters for tool '{name}'",
            data=e.errors(include_url=False, include_context=False),
        ))

    return await _default_call_tool_handler(req)

mcp._mcp_server.request_handlers[CallToolRequest] = _validating_call_tool_handler

if __name__ == "__main__":
    logging.info("Starting MCP server over STDIO")
    mcp.run(transport="stdio")
