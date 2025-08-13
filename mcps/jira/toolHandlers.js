import JiraClient from 'jira-client';
import { z } from 'zod';
import dotenv from 'dotenv';
import winston from 'winston';

// Configure logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'jira-mcp.log' })
  ]
});

// Load environment variables
dotenv.config({ path: '../../.env' });

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

// Tool definitions with schemas and handlers

// Tool: Get task details
export const getTaskTool = {
  name: 'get_task',
  config: {
    title: 'Get Jira Task',
    description: 'Get details of a Jira task by ID',
    inputSchema: {
      taskId: z.string().describe('The Jira task ID (e.g., DP-4)')
    }
  },
  handler: async ({ taskId }) => {
    logger.info(`Executing get_task tool with taskId: ${taskId}`);
    try {
      const issue = await jira.findIssue(taskId);
      
      const taskDetails = {
        id: issue.id,
        key: issue.key,
        summary: issue.fields.summary,
        attachments: JSON.stringify(issue.fields.attachment) || 'No attachments',
        description: JSON.stringify(issue.fields.description) || 'No description',
        status: issue.fields.status.name,
        assignee: issue.fields.assignee ? issue.fields.assignee.displayName : 'Unassigned',
        priority: issue.fields.priority ? issue.fields.priority.name : 'No priority',
        created: issue.fields.created,
        updated: issue.fields.updated
      };
      
      logger.info(`Successfully retrieved task ${taskId}`);
      return {
        content: [{
          type: 'text',
          text: `Task ${taskId}:\n` +
                `Summary: ${taskDetails.summary}\n` +
                `Status: ${taskDetails.status}\n` +
                `Assignee: ${taskDetails.assignee}\n` +
                `Priority: ${taskDetails.priority}\n` +
                `Attachments: ${taskDetails.attachments}\n` +
                `Description: ${taskDetails.description}\n` +
                `Created: ${taskDetails.created}\n` +
                `Updated: ${taskDetails.updated}`
        }]
      };
    } catch (error) {
      logger.error(`Error retrieving task ${taskId}: ${error.message}`);
      return {
        content: [{
          type: 'text',
          text: `Error retrieving task ${taskId}: ${error.message}`
        }]
      };
    }
  }
};

// Tool: List tasks
export const listTasksTool = {
  name: 'list_tasks',
  config: {
    title: 'List Jira Tasks',
    description: 'Get a list of Jira tasks from the project',
    inputSchema: {
      status: z.string().optional().describe('Filter tasks by status (e.g., "To Do", "In Progress")'),
      limit: z.number().optional().default(10).describe('Maximum number of tasks to return')
    }
  },
  handler: async ({ status = 'To Do', limit = 10 }) => {
    logger.info(`Executing list_tasks tool with status: ${status}, limit: ${limit}`);
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
      
      logger.info(`Successfully listed ${taskList.length} tasks with status "${status}"`);
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
      logger.error(`Error listing tasks: ${error.message}`);
      return {
        content: [{
          type: 'text',
          text: `Error listing tasks: ${error.message}`
        }]
      };
    }
  }
};

// Tool: Add comment to task
export const addCommentTool = {
  name: 'add_comment',
  config: {
    title: 'Add Comment to Jira Task',
    description: 'Add a comment to a Jira task',
    inputSchema: {
      taskId: z.string().describe('The Jira task ID'),
      comment: z.string().describe('Comment text to add')
    }
  },
  handler: async ({ taskId, comment }) => {
    logger.info(`Executing add_comment tool for task: ${taskId}`);
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
      
      logger.info(`Successfully added comment to task ${taskId}`);
      return {
        content: [{
          type: 'text',
          text: `Successfully added comment to task ${taskId}`
        }]
      };
    } catch (error) {
      logger.error(`Error adding comment to task ${taskId}: ${error.message}`);
      return {
        content: [{
          type: 'text',
          text: `Error adding comment to task ${taskId}: ${error.message}`
        }]
      };
    }
  }
};

// Tool: Get available transitions for a task
export const getTransitionsTool = {
  name: 'get_transitions',
  config: {
    title: 'Get Jira Task Transitions',
    description: 'Get available status transitions for a Jira task',
    inputSchema: {
      taskId: z.string().describe('The Jira task ID')
    }
  },
  handler: async ({ taskId }) => {
    logger.info(`Executing get_transitions tool for task: ${taskId}`);
    try {
      const transitions = await jira.listTransitions(taskId);
      
      const availableTransitions = transitions.transitions.map(transition => ({
        id: transition.id,
        name: transition.name,
        to: transition.to.name
      }));
      
      logger.info(`Successfully retrieved ${availableTransitions.length} transitions for task ${taskId}`);
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
      logger.error(`Error getting transitions for task ${taskId}: ${error.message}`);
      return {
        content: [{
          type: 'text',
          text: `Error getting transitions for task ${taskId}: ${error.message}`
        }]
      };
    }
  }
};

// Export all tools as an array for easy registration
export const tools = [
  getTaskTool,
  listTasksTool,
  addCommentTool,
  getTransitionsTool
];

// Export Jira client for potential use in tests
export { jira };
