"""Fixed values for the MCP server and its call log."""

MCP_SERVER_NAME = "voxlabs"
# Port of the standalone MCP server (`voxlabs-mcp --http`); the REST API's /mcp uses the API port.
MCP_HTTP_PORT = 8943
# Calls kept in `mcp_calls`; older ones are removed as new ones arrive.
MCP_LOG_LIMIT = 2000
# Longest text kept per argument or result value in the log (the rest is cut with "…").
MCP_LOG_TEXT_CHARS = 500
# Argument names whose values are never logged.
MCP_SECRET_FIELDS = ("token", "password", "secret", "authorization", "api_key")
