#!/usr/bin/env node

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import JiraClient from 'jira-client';
import { z } from 'zod';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';

// Load environment variables
dotenv.config({ path: '../../.env' });

// Create logs directory if it doesn't exist
const logsDir = path.join(process.cwd(), 'logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

const logFile = path.join(logsDir, 'jira-mcp.log');

// Logging utility
function log(level, toolName, message, data = null) {
  const timestamp = new Date().toISOString();
  const logEntry = {
    timestamp,
    level,
    service: 'jira-mcp',
    tool: toolName,
    message,
    ...(data && { data })
  };
  
  const logLine = `[JIRA-MCP ${level.toUpperCase()}] ${JSON.stringify(logEntry)}\n`;
  
  try {
    fs.appendFileSync(logFile, logLine);
  } catch (error) {
    // Fallback to stderr only if file logging fails
    console.error(`Failed to write to log file: ${error.message}`);
  }
}

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
    log('info', 'get_task', 'Tool called', { taskId });
    
    try {
      log('info', 'get_task', 'Calling jira.findIssue', { taskId });
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
      
      log('info', 'get_task', 'Successfully retrieved task', { 
        taskId, 
        summary: taskDetails.summary, 
        status: taskDetails.status 
      });
      
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
      log('error', 'get_task', 'Failed to retrieve task', { 
        taskId, 
        error: error.message,
        stack: error.stack 
      });
      
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
    log('info', 'list_tasks', 'Tool called', { status, limit });
    
    try {
      const jql = `project = ${process.env.JIRA_PROJECT} AND status = "${status}" ORDER BY created DESC`;
      log('info', 'list_tasks', 'Executing JQL query', { jql, maxResults: limit });
      
      const issues = await jira.searchJira(jql, { maxResults: limit });
      
      const taskList = issues.issues.map(issue => ({
        key: issue.key,
        summary: issue.fields.summary,
        status: issue.fields.status.name,
        assignee: issue.fields.assignee ? issue.fields.assignee.displayName : 'Unassigned',
        priority: issue.fields.priority ? issue.fields.priority.name : 'No priority'
      }));
      
      log('info', 'list_tasks', 'Successfully retrieved tasks', { 
        status, 
        count: taskList.length,
        taskKeys: taskList.map(t => t.key)
      });
      
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
      log('error', 'list_tasks', 'Failed to list tasks', { 
        status, 
        limit,
        error: error.message,
        stack: error.stack 
      });
      
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
    log('info', 'add_comment', 'Tool called', { taskId, commentLength: comment.length });
    
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

      log('info', 'add_comment', 'Adding comment to Jira', { taskId, commentBody });
      
      // Use the Jira client's addComment method with ADF format
      await jira.addComment(taskId, commentBody);
      
      log('info', 'add_comment', 'Successfully added comment', { taskId });
      
      return {
        content: [{
          type: 'text',
          text: `Successfully added comment to task ${taskId}`
        }]
      };
    } catch (error) {
      log('error', 'add_comment', 'Failed to add comment', { 
        taskId, 
        error: error.message,
        stack: error.stack 
      });
      
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
    log('info', 'get_transitions', 'Tool called', { taskId });
    
    try {
      log('info', 'get_transitions', 'Calling jira.listTransitions', { taskId });
      const transitions = await jira.listTransitions(taskId);
      
      const availableTransitions = transitions.transitions.map(transition => ({
        id: transition.id,
        name: transition.name,
        to: transition.to.name
      }));
      
      log('info', 'get_transitions', 'Successfully retrieved transitions', { 
        taskId, 
        transitionCount: availableTransitions.length,
        transitions: availableTransitions
      });
      
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
      log('error', 'get_transitions', 'Failed to get transitions', { 
        taskId, 
        error: error.message,
        stack: error.stack 
      });
      
      return {
        content: [{
          type: 'text',
          text: `Error getting transitions for task ${taskId}: ${error.message}`
        }]
      };
    }
  }
);

// Start the STDIO MCP server
async function main() {
  log('info', 'startup', 'Starting Jira MCP server', {
    jiraUrl: jiraUrl || 'NOT_CONFIGURED',
    jiraProject: process.env.JIRA_PROJECT || 'NOT_CONFIGURED',
    jiraUsername: process.env.JIRA_USERNAME ? 'CONFIGURED' : 'NOT_CONFIGURED'
  });
  
  // Create STDIO transport
  const transport = new StdioServerTransport();
  
  // Connect the server to the transport
  await server.connect(transport);
  
  log('info', 'startup', 'Jira MCP server started successfully with STDIO transport');
  console.error('Jira MCP server started with STDIO transport');
}

main().catch((error) => {
  log('error', 'startup', 'Failed to start Jira MCP server', {
    error: error.message,
    stack: error.stack
  });
  console.error('Failed to start Jira MCP server:', error);
  process.exit(1);
});
