import { z } from 'zod';
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

export function registerJiraTools(server, jira) {
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
      logger.info(`get_task: invoked taskId=${taskId}`, { taskId });
      try {
        const issue = await jira.findIssue(taskId);

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

        logger.info(`get_task: success taskId=${taskId}`, { key: taskDetails.key, status: taskDetails.status });
        return {
          content: [{
            type: 'text',
            text: `Task ${taskId}:\n` +
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
        logger.error(`get_task: error taskId=${taskId}`, { message: error.message, stack: error.stack });
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
      logger.info(`add_comment: invoked taskId=${taskId} commentLength=${comment?.length ?? 0}`);
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

        logger.info(`add_comment: success taskId=${taskId}`);
        return {
          content: [{
            type: 'text',
            text: `Successfully added comment to task ${taskId}`
          }]
        };
      } catch (error) {
        logger.error(`add_comment: error taskId=${taskId}`, { message: error.message, stack: error.stack });
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
      logger.info(`get_transitions: invoked taskId=${taskId}`);
      try {
        const transitions = await jira.listTransitions(taskId);

        const availableTransitions = transitions.transitions.map(transition => ({
          id: transition.id,
          name: transition.name,
          to: transition.to.name
        }));

        logger.info(`get_transitions: success count=${availableTransitions.length} taskId=${taskId}`);
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
        logger.error(`get_transitions: error taskId=${taskId}`, { message: error.message, stack: error.stack });
        return {
          content: [{
            type: 'text',
            text: `Error getting transitions for task ${taskId}: ${error.message}`
          }]
        };
      }
    }
  );
}
