#!/usr/bin/env node

import express from 'express';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import JiraClient from 'jira-client';
import dotenv from 'dotenv';
import { registerJiraTools } from './tools.js';

// Load environment variables
dotenv.config({ path: '../../.env' });

// Initialize Express app
const app = express();
app.use(express.json());
// Logging middleware to trace MCP client-server interactions
app.use((req, res, next) => {
  const start = Date.now();
  const sessionId = req.header('mcp-session-id') || '(none)';
  const method = req.method;
  const path = req.path;
  
  // Log request with headers
  try {
    if (path === '/mcp') {
      const headers = JSON.stringify(req.headers);
      if (method === 'POST') {
        console.log(`[MCP] -> ${method} ${path} sid=${sessionId} headers=${headers} body=${JSON.stringify(req.body)}`);
      } else {
        console.log(`[MCP] -> ${method} ${path} sid=${sessionId} headers=${headers}`);
      }
    }
  } catch {
    console.log(`[MCP] -> ${method} ${path} sid=${sessionId} (logging failed)`);
  }
  
  // Log response with status and duration
  res.on('finish', () => {
    const duration = Date.now() - start;
    try {
      const responseHeaders = JSON.stringify(res.getHeaders());
      const responseBody = res.body ? JSON.stringify(res.body) : '';
      console.log(`[MCP] <- ${method} ${path} sid=${sessionId} status=${res.statusCode} headers=${responseHeaders} ${duration}ms body=${responseBody}`);
    } catch (error) {
      console.log(`[MCP] <- ${method} ${path} sid=${sessionId} status=${res.statusCode} ${duration}ms (logging failed)`);
    }
  });
  next();
});

// Health check route
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', service: 'jira-mcp' });
});

// Initialize Jira client
const jiraUrl = process.env.JIRA_URL ? process.env.JIRA_URL.replace(/^https?:\/\//, '') : '';
const jira = new JiraClient({
  protocol: 'https',
  host: jiraUrl,
  username: process.env.JIRA_USERNAME,
  password: process.env.JIRA_API_TOKEN,
  apiVersion: '3',
  strictSSL: true
});

// Create MCP server instance
const server = new McpServer({
  name: 'jira-mcp',
  version: '1.0.0'
});

// Register Jira tools
registerJiraTools(server, jira);

// Create transport (client provides mcp-session-id; no server-side generation)
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: undefined,
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
    await transport.handleRequest(req, res);
  } catch (error) {
    console.error('Error handling session deletion:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});


// Start the HTTP MCP server
async function main() {
  const port = process.env.PORT || 3003;
  
  // Connect the transport to the MCP server
  await server.connect(transport);
  
  // Start Express server
  app.listen(port, () => {
    console.log(`Jira MCP server listening on http://localhost:${port}`);
  });
}

main().catch((error) => {
  console.error('Failed to start Jira MCP server:', error);
  process.exit(1);
});
