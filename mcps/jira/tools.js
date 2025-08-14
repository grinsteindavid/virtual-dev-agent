import { z } from 'zod';
import winston from 'winston';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import JiraClient from 'jira-client';

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

/**
 * Register Jira tools with the MCP server
 * @param {McpServer} server - The MCP server instance
 * @param {JiraClient} jira - Initialized Jira client
 */
export function registerJiraTools(server, jira) {
  // Tool: Get task details
  server.registerTool(
    'get_task',
    {
      title: 'Get Jira Task',
      description: 'Get details of a Jira task by ID',
      inputSchema: {
        task_id: z.string().describe('The Jira task ID (e.g., DP-4)')
      }
    },
    async ({ task_id }) => {
      logger.info(`get_task: invoked task_id=${task_id}`, { task_id });
      try {
        const issue = await jira.findIssue(task_id);

        const taskDetails = {
          id: issue.id,
          key: issue.key,
          summary: issue.fields.summary,
          description: JSON.stringify(issue.fields.description) || 'No description',
          attachments: JSON.stringify(issue.fields.attachment) || 'No attachments',
          status: issue.fields.status.name,
          assignee: issue.fields.assignee ? issue.fields.assignee.displayName : 'Unassigned',
          priority: issue.fields.priority ? issue.fields.priority.name : 'No priority',
          created: issue.fields.created,
          updated: issue.fields.updated
        };

        logger.info(`get_task: success task_id=${task_id}`, { key: taskDetails.key, status: taskDetails.status, task_id });
        return {
          content: [{
            type: 'text',
            text: `Task ${task_id}:\n` +
                  `Summary: ${taskDetails.summary}\n` +
                  `Status: ${taskDetails.status}\n` +
                  `Assignee: ${taskDetails.assignee}\n` +
                  `Priority: ${taskDetails.priority}\n` +
                  `Description: ${taskDetails.description}\n` +
                  `Attachments: ${taskDetails.attachments}\n` +
                  `Created: ${taskDetails.created}\n` +
                  `Updated: ${taskDetails.updated}`
          }]
        };
      } catch (error) {
        logger.error(`get_task: error task_id=${task_id}`, { message: error.message, stack: error.stack, task_id });
        return {
          content: [{
            type: 'text',
            text: `Error retrieving task ${task_id}: ${error.message}`
          }]
        };
      }
    }
  );

  // Tool: List tasks
  server.registerTool(
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
      logger.info(`list_tasks: invoked status=${status} limit=${limit}`);
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

        logger.info(`list_tasks: success count=${taskList.length} status=${status}`);
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
        logger.error(`list_tasks: error status=${status}`, { message: error.message, stack: error.stack });
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
  server.registerTool(
    'add_comment',
    {
      title: 'Add Comment to Jira Task',
      description: 'Add a comment to a Jira task',
      inputSchema: {
        task_id: z.string().describe('The Jira task ID'),
        comment: z.string().describe('Comment text to add')
      }
    },
    async ({ task_id, comment }) => {
      logger.info(`add_comment: invoked task_id=${task_id} commentLength=${comment?.length ?? 0}`);
      try {
        // Using Jira API v2 format for comments (simple string)
        const commentBody = comment;

        // Use the Jira client's addComment method with v2 API format
        await jira.addComment(task_id, commentBody);

        logger.info(`add_comment: success task_id=${task_id}`);
        return {
          content: [{
            type: 'text',
            text: `Successfully added comment to task ${task_id}`
          }]
        };
      } catch (error) {
        logger.error(`add_comment: error task_id=${task_id}`, { message: error.message, stack: error.stack, task_id });
        return {
          content: [{
            type: 'text',
            text: `Error adding comment to task ${task_id}: ${error.message}`
          }]
        };
      }
    }
  );

  // Tool: Get available transitions for a task
  server.registerTool(
    'get_transitions',
    {
      title: 'Get Jira Task Transitions',
      description: 'Get available status transitions for a Jira task',
      inputSchema: {
        task_id: z.string().describe('The Jira task ID')
      }
    },
    async ({ task_id }) => {
      logger.info(`get_transitions: invoked task_id=${task_id}`);
      try {
        const transitions = await jira.listTransitions(task_id);

        const availableTransitions = transitions.transitions.map(transition => ({
          id: transition.id,
          name: transition.name,
          to: transition.to.name
        }));

        logger.info(`get_transitions: success count=${availableTransitions.length} task_id=${task_id}`);
        return {
          content: [{
            type: 'text',
            text: `Available transitions for task ${task_id}:\n\n` +
                  availableTransitions.map(transition => 
                    `ID: ${transition.id}\n` +
                    `Name: ${transition.name}\n` +
                    `To Status: ${transition.to}\n`
                  ).join('\n')
          }]
        };
      } catch (error) {
        logger.error(`get_transitions: error task_id=${task_id}`, { message: error.message, stack: error.stack, task_id });
        return {
          content: [{
            type: 'text',
            text: `Error getting transitions for task ${task_id}: ${error.message}`
          }]
        };
      }
    }
  );

  // Tool: Transition task status
  server.tool(
    'transition_task_status',
    {
      title: 'Transition Jira Task Status',
      description: 'Change the status of a Jira task using transition ID',
      inputSchema: {
        task_id: z.string().describe('The Jira task ID'),
        transition_id: z.string().describe('The transition ID to execute (must be convertible to an integer)'),
        comment: z.string().optional().describe('Optional comment to add with the transition')
      }
    },
    async ({ task_id, transition_id, comment }) => {
      logger.info(`transition_task_status: invoked task_id=${task_id} transition_id=${transition_id}`);
      
      // Validate required parameters
      if (!task_id) {
        logger.error('transition_task_status: missing task_id parameter');
        return {
          content: [{
            type: 'text',
            text: 'Error: task_id parameter is required'
          }]
        };
      }
      
      if (!transition_id) {
        logger.error('transition_task_status: missing transition_id parameter');
        return {
          content: [{
            type: 'text',
            text: 'Error: transition_id parameter is required'
          }]
        };
      }
      
      // Convert transition_id to integer
      const transitionIdInt = parseInt(transition_id, 10);
      if (isNaN(transitionIdInt)) {
        logger.error(`transition_task_status: invalid transition_id=${transition_id}, not a valid integer`);
        return {
          content: [{
            type: 'text',
            text: `Error: transition_id must be a valid integer, received: ${transition_id}`
          }]
        };
      }
      
      try {
        // Prepare transition data with integer transition ID
        const transitionData = {
          transition: {
            id: transitionIdInt
          }
        };
        
        // Add comment if provided
        if (comment) {
          transitionData.update = {
            comment: comment
          };
        }

        // Execute the transition
        await jira.transitionIssue(task_id, transitionData);
        
        // Get updated task details to confirm the new status
        const updatedIssue = await jira.findIssue(task_id);
        const newStatus = updatedIssue.fields.status.name;
        
        logger.info(`transition_task_status: success task_id=${task_id} new_status=${newStatus}`);
        return {
          content: [{
            type: 'text',
            text: `Successfully transitioned task ${task_id} to status: ${newStatus}`
          }]
        };
      } catch (error) {
        logger.error(`transition_task_status: error task_id=${task_id}`, { message: error.message, stack: error.stack, task_id, transition_id });
        return {
          content: [{
            type: 'text',
            text: `Error transitioning task ${task_id}: ${error.message}`
          }]
        };
      }
    }
  );
}
