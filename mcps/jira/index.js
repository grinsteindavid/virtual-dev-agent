#!/usr/bin/env node

import express from 'express';
import { randomUUID } from 'crypto';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import JiraClient from 'jira-client';
import { z } from 'zod';
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

// Function to create a new MCP server instance
function createMcpServer() {
  const server = new McpServer({
    name: 'jira-mcp',
    version: '1.0.0'
  });

  // Register Jira tools

  // Tool: Get task details
  server.tool(
  'get_task',
  {
    title: 'Get Jira Task',
    description: 'Get details of a Jira task by ID',
    inputSchema: {
      taskId: z.string().describe('The Jira task ID (e.g., DP-4)')
    }
  },
  async ({ taskId }) => {
    try {
      const issue = await jira.findIssue(taskId);
      
      const taskDetails = {
        id: issue.id,
        key: issue.key,
        summary: issue.fields.summary,
        description: issue.fields.description || 'No description',
        status: issue.fields.status.name,
        assignee: issue.fields.assignee ? issue.fields.assignee.displayName : 'Unassigned',
        priority: issue.fields.priority ? issue.fields.priority.name : 'No priority',
        created: issue.fields.created,
        updated: issue.fields.updated
      };
      
      return {
        content: [{
          type: 'text',
          text: `Task ${taskId}:\n` +
                `Summary: ${taskDetails.summary}\n` +
                `Status: ${taskDetails.status}\n` +
                `Assignee: ${taskDetails.assignee}\n` +
                `Priority: ${taskDetails.priority}\n` +
                `Description: ${taskDetails.description}\n` +
                `Created: ${taskDetails.created}\n` +
                `Updated: ${taskDetails.updated}`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error retrieving task ${taskId}: ${error.message}`
        }]
      };
    }
  }
);

  // Tool: List tasks
  server.tool(
  'list_tasks',
  {
    title: 'List Jira Tasks',
    description: 'Get a list of Jira tasks from the project',
    inputSchema: {
      status: z.string().optional().describe('Filter tasks by status (e.g., "To Do", "In Progress")'),
      limit: z.number().optional().default(10).describe('Maximum number of tasks to return')
    }
  },
  async ({ status = 'To Do', limit = 10 }) => {
    try {
      const jql = `project = ${process.env.JIRA_PROJECT} AND status = "${status}" ORDER BY created DESC`;
      const issues = await jira.searchJira(jql, { maxResults: limit });
      
      const taskList = issues.issues.map(issue => ({
        key: issue.key,
        summary: issue.fields.summary,
        status: issue.fields.status.name,
        assignee: issue.fields.assignee ? issue.fields.assignee.displayName : 'Unassigned',
        priority: issue.fields.priority ? issue.fields.priority.name : 'No priority'
      }));
      
      return {
        content: [{
          type: 'text',
          text: `Found ${taskList.length} tasks with status "${status}":\n\n` +
                taskList.map(task => 
                  `${task.key}: ${task.summary}\n` +
                  `  Status: ${task.status}\n` +
                  `  Assignee: ${task.assignee}\n` +
                  `  Priority: ${task.priority}\n`
                ).join('\n')
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error listing tasks: ${error.message}`
        }]
      };
    }
  }
);

  // Tool: Add comment to task
  server.tool(
  'add_comment',
  {
    title: 'Add Comment to Jira Task',
    description: 'Add a comment to a Jira task',
    inputSchema: {
      taskId: z.string().describe('The Jira task ID'),
      comment: z.string().describe('Comment text to add')
    }
  },
  async ({ taskId, comment }) => {
    try {
      // Create Atlassian Document Format (ADF) JSON structure for the comment
      const commentBody = {
        body: {
          type: 'doc',
          version: 1,
          content: [
            {
              type: 'paragraph',
              content: [
                {
                  type: 'text',
                  text: comment
                }
              ]
            }
          ]
        }
      };

      // Use the Jira client's addComment method with ADF format
      await jira.addComment(taskId, commentBody);
      
      return {
        content: [{
          type: 'text',
          text: `Successfully added comment to task ${taskId}`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error adding comment to task ${taskId}: ${error.message}`
        }]
      };
    }
  }
);

  // Tool: Get available transitions for a task
  server.tool(
  'get_transitions',
  {
    title: 'Get Jira Task Transitions',
    description: 'Get available status transitions for a Jira task',
    inputSchema: {
      taskId: z.string().describe('The Jira task ID')
    }
  },
  async ({ taskId }) => {
    try {
      const transitions = await jira.listTransitions(taskId);
      
      const availableTransitions = transitions.transitions.map(transition => ({
        id: transition.id,
        name: transition.name,
        to: transition.to.name
      }));
      
      return {
        content: [{
          type: 'text',
          text: `Available transitions for task ${taskId}:\n\n` +
                availableTransitions.map(transition => 
                  `ID: ${transition.id}\n` +
                  `Name: ${transition.name}\n` +
                  `To Status: ${transition.to}\n`
                ).join('\n')
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error getting transitions for task ${taskId}: ${error.message}`
        }]
      };
    }
  });

  return server;
}

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

// Create and connect a single MCP server instance to the transport
const server = createMcpServer();

// Handle POST requests for JSON-RPC
app.post('/mcp', async (req, res) => {
  try {
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
      // Clean up the session
      sessions.delete(sessionId);
      console.log(`Session ${sessionId} ended and cleaned up`);
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
  
  // Connect the server to the transport
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
