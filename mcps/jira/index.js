#!/usr/bin/env node

import express from 'express';
import { randomUUID } from 'crypto';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { tools } from './toolHandlers.js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config({ path: '../../.env' });

// Initialize Express app
const app = express();
app.use(express.json());

// Health check route
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', service: 'jira-mcp' });
});

// Store active sessions
const sessions = new Map();

// Session management functions
const sessionIdGenerator = () => randomUUID();

const onSessionInitialized = async (sessionId, transport) => {
  console.log(`New session initialized: ${sessionId}`);
  
  // Create a new MCP server instance for this session
  const sessionServer = new McpServer({
    name: 'jira-mcp',
    version: '1.0.0'
  });
  
  // Register all tools for this session's server
  tools.forEach(tool => {
    sessionServer.tool(
      tool.name,
      tool.config,
      tool.handler
    );
  });
  
  // Connect this session's server to the transport
  await sessionServer.connect(transport);
  
  // Store both transport and server in the session
  sessions.set(sessionId, { 
    transport, 
    server: sessionServer,
    createdAt: new Date() 
  });
};

// Create transport with automatic session ID management
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator,
  onSessionInitialized
});

// Handle POST requests for JSON-RPC
app.post('/mcp', async (req, res) => {
  try {
    // The transport will automatically handle session IDs
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.error('Error handling MCP request:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// Handle GET requests for SSE streaming
app.get('/mcp', async (req, res) => {
  try {
    await transport.handleRequest(req, res);
  } catch (error) {
    console.error('Error handling SSE request:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// Handle DELETE requests to end sessions
app.delete('/mcp', async (req, res) => {
  try {
    const sessionId = req.headers['mcp-session-id'];
    if (sessionId && sessions.has(sessionId)) {
      const session = sessions.get(sessionId);
      if (session.server) {
        await session.server.close();
      }
      sessions.delete(sessionId);
      console.log(`Session ${sessionId} closed and removed`);
    }
    await transport.handleRequest(req, res);
  } catch (error) {
    console.error('Error handling session deletion:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});


// Start the HTTP MCP server
async function main() {
  const port = process.env.PORT || 3003;
  
  // Start Express server
  app.listen(port, () => {
    console.log(`Jira MCP server listening on http://localhost:${port}`);
  });
}

main().catch((error) => {
  console.error('Failed to start Jira MCP server:', error);
  process.exit(1);
});
