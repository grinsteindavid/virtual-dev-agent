#!/usr/bin/env node

import express from 'express';
import { randomUUID } from 'crypto';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { Octokit } from '@octokit/rest';
import { z } from 'zod';
import dotenv from 'dotenv';

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
    const responseHeaders = JSON.stringify(res.getHeaders());
    console.log(`[MCP] <- ${method} ${path} sid=${sessionId} status=${res.statusCode} headers=${responseHeaders} ${duration}ms`);
  });
  next();
});

// Health check route
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', service: 'github-mcp' });
});

// Initialize GitHub client
const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN
});

// Create MCP server instance
const server = new McpServer({
  name: 'github-mcp',
  version: '1.0.0'
});

// Register GitHub tools

// Tool: Get repository information
server.registerTool(
  'get_repo_info',
  {
    title: 'Get Repository Info',
    description: 'Get information about a GitHub repository',
    inputSchema: {
      owner: z.string().describe('Repository owner/organization'),
      repo: z.string().describe('Repository name')
    }
  },
  async ({ owner, repo }) => {
    try {
      const { data } = await octokit.rest.repos.get({
        owner,
        repo
      });
      
      return {
        content: [{
          type: 'text',
          text: `Repository: ${data.full_name}\n` +
                `Description: ${data.description || 'No description'}\n` +
                `Language: ${data.language || 'Not specified'}\n` +
                `Stars: ${data.stargazers_count}\n` +
                `Forks: ${data.forks_count}\n` +
                `Open Issues: ${data.open_issues_count}\n` +
                `Created: ${data.created_at}\n` +
                `Updated: ${data.updated_at}\n` +
                `URL: ${data.html_url}`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error getting repository info: ${error.message}`
        }]
      };
    }
  }
);

// Tool: List issues
server.registerTool(
  'list_issues',
  {
    title: 'List GitHub Issues',
    description: 'List issues in a GitHub repository',
    inputSchema: {
      owner: z.string().describe('Repository owner/organization'),
      repo: z.string().describe('Repository name'),
      state: z.string().optional().default('open').describe('Issue state (open, closed, all)'),
      limit: z.number().optional().default(10).describe('Maximum number of issues to return')
    }
  },
  async ({ owner, repo, state = 'open', limit = 10 }) => {
    try {
      const { data } = await octokit.rest.issues.listForRepo({
        owner,
        repo,
        state,
        per_page: limit
      });
      
      const issues = data.map(issue => ({
        number: issue.number,
        title: issue.title,
        state: issue.state,
        author: issue.user.login,
        created: issue.created_at,
        url: issue.html_url
      }));
      
      return {
        content: [{
          type: 'text',
          text: `Found ${issues.length} issues in ${owner}/${repo}:\n\n` +
                issues.map(issue => 
                  `#${issue.number}: ${issue.title}\n` +
                  `  State: ${issue.state}\n` +
                  `  Author: ${issue.author}\n` +
                  `  Created: ${issue.created}\n` +
                  `  URL: ${issue.url}\n`
                ).join('\n')
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error listing issues: ${error.message}`
        }]
      };
    }
  }
);

// Tool: Create issue
server.registerTool(
  'create_issue',
  {
    title: 'Create GitHub Issue',
    description: 'Create a new issue in a GitHub repository',
    inputSchema: {
      owner: z.string().describe('Repository owner/organization'),
      repo: z.string().describe('Repository name'),
      title: z.string().describe('Issue title'),
      body: z.string().optional().describe('Issue body/description')
    }
  },
  async ({ owner, repo, title, body }) => {
    try {
      const { data } = await octokit.rest.issues.create({
        owner,
        repo,
        title,
        body
      });
      
      return {
        content: [{
          type: 'text',
          text: `Successfully created issue #${data.number}: ${data.title}\n` +
                `URL: ${data.html_url}`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error creating issue: ${error.message}`
        }]
      };
    }
  }
);

// Tool: Create pull request
server.registerTool(
  'create_pull_request',
  {
    title: 'Create GitHub Pull Request',
    description: 'Create a new pull request in a GitHub repository',
    inputSchema: {
      owner: z.string().describe('Repository owner/organization'),
      repo: z.string().describe('Repository name'),
      title: z.string().describe('Pull request title'),
      body: z.string().optional().describe('Pull request body/description'),
      head: z.string().describe('Branch to merge from (source branch)'),
      base: z.string().optional().default('main').describe('Branch to merge into (target branch, default: main)')
    }
  },
  async ({ owner, repo, title, body, head, base = 'main' }) => {
    try {
      const { data } = await octokit.rest.pulls.create({
        owner,
        repo,
        title,
        body,
        head,
        base
      });
      
      return {
        content: [{
          type: 'text',
          text: `Successfully created pull request #${data.number}: ${data.title}\n` +
                `From: ${data.head.ref} → ${data.base.ref}\n` +
                `State: ${data.state}\n` +
                `URL: ${data.html_url}`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error creating pull request: ${error.message}`
        }]
      };
    }
  }
);

// Store active sessions
const sessions = new Map();

// Session management functions
const sessionIdGenerator = () => randomUUID();

const onSessionInitialized = (sessionId, transport) => {
  console.log(`New session initialized: ${sessionId}`);
  sessions.set(sessionId, { transport, createdAt: new Date() });
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
    await transport.handleRequest(req, res);
  } catch (error) {
    console.error('Error handling session deletion:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});


// Start the HTTP MCP server
async function main() {
  const port = process.env.PORT || 3002;
  
  // Connect the transport to the MCP server
  await server.connect(transport);
  
  // Start Express server
  app.listen(port, () => {
    console.log(`GitHub MCP server listening on http://localhost:${port}`);
  });
}

main().catch((error) => {
  console.error('Failed to start GitHub MCP server:', error);
  process.exit(1);
});
