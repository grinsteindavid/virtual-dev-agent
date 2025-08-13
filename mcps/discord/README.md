# Discord MCP Server

A Model Context Protocol (MCP) server for Discord integration with automatic session management.

## Features

- Automatic session ID generation and management
- Express integration for HTTP endpoints
- Support for Discord webhook messaging
- Stateful mode with session tracking

## Session Management

This implementation uses StreamableHTTPServerTransport in stateful mode with automatic session ID management:

### How Session Management Works

1. **First Request**:
   - Client makes a request without an `mcp-session-id` header
   - Server generates a new session ID using `randomUUID()`
   - Server includes the session ID in the response headers
   - Session is stored in the sessions Map

2. **Subsequent Requests**:
   - Client includes the previously received `mcp-session-id` in request headers
   - Server identifies the existing session and reuses it
   - State is maintained across requests (connections, message history)

3. **Session Endpoints**:
   - `POST /mcp` - For JSON-RPC requests
   - `GET /mcp` - For SSE streaming
   - `DELETE /mcp` - For ending sessions

### Implementation Details

The server uses the following key components for session management:

```javascript
// Session generation function
const sessionIdGenerator = () => randomUUID();

// Session initialization callback
const onSessionInitialized = (sessionId, transport) => {
  console.log(`New session initialized: ${sessionId}`);
  sessions.set(sessionId, { transport, createdAt: new Date() });
};

// Create transport with automatic session ID management
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator,
  onSessionInitialized
});
```

## Usage

1. Install dependencies:
   ```
   npm install
   ```

2. Run the server:
   ```
   npm start
   ```

3. The server will be available at http://localhost:3001/mcp

## Environment Variables

- `PORT` - Server port (default: 3001)
- `DISCORD_WEBHOOK_URL` - Discord webhook URL for sending messages
