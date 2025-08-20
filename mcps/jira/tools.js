import { z } from 'zod';
import winston from 'winston';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import JiraClient from 'jira-client';

import axios from 'axios';
import fs from 'node:fs';
import path from 'node:path';

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
  // Get task details
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
          comments: JSON.stringify(issue.fields.comment) || 'No comments',
          status: issue.fields.status.name,
          changelog: JSON.stringify(issue.fields.changelog) || 'No changelog',
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
                  `Comments: ${taskDetails.comments}\n` +
                  `Changelog: ${taskDetails.changelog}\n` +
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

  // List tasks
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

  // Add comment to task
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

  // Get available transitions for a task
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

  // Transition task status
  server.registerTool(
    'transition_task_status',
    {
      title: 'Transition Jira Task Status',
      description: 'Change the status of a Jira task using transition ID',
      inputSchema: {
        task_id: z.string().describe('The Jira task ID'),
        transition_id: z.string().describe('The transition ID to execute (must be convertible to an integer)'),
      }
    },
    async ({ task_id, transition_id }) => {
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
      
      // Validate that transition_id is numeric (Jira transition IDs are numeric strings)
      if (!/^\d+$/.test(String(transition_id))) {
        logger.error(`transition_task_status: invalid transition_id=${transition_id}, must be a numeric string`);
        return {
          content: [{
            type: 'text',
            text: `Error: transition_id must be a numeric string, received: ${transition_id}`
          }]
        };
      }
      
      try {
        // Prepare transition data with integer transition ID
        const transitionData = {
          transition: {
            id: String(transition_id)
          }
        };

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

  // Download image attachments for a task
  server.registerTool(
    'download_image_attachments',
    {
      title: 'Download Jira Image Attachments',
      description: 'Download all image attachments for a Jira task to a local directory (default: /tmp). Returns saved file paths.',
      inputSchema: {
        task_id: z.string().describe('The Jira task ID (e.g., DP-4)'),
        dest_dir: z.string().default('/tmp').optional().describe('Destination directory to save files (default: /tmp)')
      }
    },
    async ({ task_id, dest_dir = '/tmp' }) => {
      logger.info(`download_image_attachments: invoked task_id=${task_id} dest_dir=${dest_dir}`);
      try {
        // Ensure destination directory exists
        await fs.promises.mkdir(dest_dir, { recursive: true });

        // Fetch issue to inspect attachments
        const issue = await jira.findIssue(task_id);
        const attachments = issue?.fields?.attachment ?? [];

        const exts = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg'];
        const isImage = (att) => {
          const mt = String(att?.mimeType || '');
          if (mt.startsWith('image/')) return true;
          const name = String(att?.filename || att?.fileName || '');
          const lower = name.toLowerCase();
          return exts.some(ext => lower.endsWith(ext));
        };

        const imageAttachments = attachments.filter(isImage);
        if (imageAttachments.length === 0) {
          logger.info(`download_image_attachments: no image attachments task_id=${task_id}`);
          return {
            content: [{
              type: 'text',
              text: `No image attachments found for task ${task_id}`
            }]
          };
        }

        const authHeader = 'Basic ' + Buffer.from(`${process.env.JIRA_USERNAME}:${process.env.JIRA_API_TOKEN}`).toString('base64');
        const savedPaths = [];

        for (const att of imageAttachments) {
          const url = att.content;
          const baseName = (att.filename || att.fileName || `attachment-${att.id || ''}`).toString();
          const safeName = baseName.replace(/[^a-zA-Z0-9._-]/g, '_');
          const finalName = `${task_id}-${safeName}`;
          const destPath = path.join(dest_dir, finalName);

          logger.info(`download_image_attachments: downloading ${url} -> ${destPath}`);

          const response = await axios({
            method: 'get',
            url,
            responseType: 'stream',
            headers: { 'Authorization': authHeader },
            timeout: 60000,
            maxRedirects: 5
          });

          await new Promise((resolve, reject) => {
            const writer = fs.createWriteStream(destPath);
            response.data.pipe(writer);
            writer.on('finish', resolve);
            writer.on('error', reject);
          });

          savedPaths.push(destPath);
        }

        logger.info(`download_image_attachments: success task_id=${task_id} count=${savedPaths.length}`);
        return {
          content: [{
            type: 'text',
            text: `Downloaded ${savedPaths.length} image attachment(s) for ${task_id} to ${dest_dir}:\n` + savedPaths.map(p => `- ${p}`).join('\n')
          }]
        };
      } catch (error) {
        logger.error(`download_image_attachments: error task_id=${task_id}`, { message: error.message, stack: error.stack, task_id, dest_dir });
        return {
          content: [{
            type: 'text',
            text: `Error downloading image attachments for ${task_id}: ${error.message}`
          }]
        };
      }
    }
  );

  // Download attachments (images, pdf, csv, or all)
  server.registerTool(
    'download_attachments',
    {
      title: 'Download Jira Attachments',
      description: 'Download attachments filtered by types (image, pdf, csv, or all) to a local directory (default: /tmp). Returns saved file paths.',
      inputSchema: {
        task_id: z.string().describe('The Jira task ID (e.g., DP-4)'),
        types: z.array(z.enum(['image', 'pdf', 'csv', 'all']))
          .optional()
          .default(['image', 'pdf', 'csv'])
          .describe('Attachment types to download. Include "all" to download everything.'),
        dest_dir: z.string().optional().default('/tmp').describe('Destination directory to save files (default: /tmp)')
      }
    },
    async ({ task_id, types = ['image', 'pdf', 'csv'], dest_dir = '/tmp' }) => {
      logger.info(`download_attachments: invoked task_id=${task_id} types=${Array.isArray(types) ? types.join(',') : String(types)} dest_dir=${dest_dir}`);
      try {
        await fs.promises.mkdir(dest_dir, { recursive: true });

        // Fetch issue and attachments
        const issue = await jira.findIssue(task_id);
        const attachments = issue?.fields?.attachment ?? [];

        const imageExts = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg', '.tif', '.tiff', '.ico', '.heic', '.heif'];
        const pdfExts = ['.pdf'];
        const csvExts = ['.csv'];

        const hasExt = (name, exts) => {
          const lower = String(name || '').toLowerCase();
          return exts.some(ext => lower.endsWith(ext));
        };

        const isType = (att, t) => {
          const mime = String(att?.mimeType || '');
          const name = String(att?.filename || att?.fileName || '');
          switch (t) {
            case 'image':
              return mime.startsWith('image/') || hasExt(name, imageExts);
            case 'pdf':
              return mime.includes('pdf') || hasExt(name, pdfExts);
            case 'csv':
              return mime === 'text/csv' || hasExt(name, csvExts);
            default:
              return false;
          }
        };

        const selected = Array.isArray(types) ? types : [types];
        const matchAll = selected.includes('all');
        const filtered = attachments.filter(att => matchAll || selected.some(t => isType(att, t)));

        if (filtered.length === 0) {
          logger.info(`download_attachments: no matching attachments task_id=${task_id}`);
          return {
            content: [{
              type: 'text',
              text: `No attachments of requested types found for task ${task_id}`
            }]
          };
        }

        const authHeader = 'Basic ' + Buffer.from(`${process.env.JIRA_USERNAME}:${process.env.JIRA_API_TOKEN}`).toString('base64');
        const savedPaths = [];

        for (const att of filtered) {
          const url = att.content;
          const baseName = (att.filename || att.fileName || `attachment-${att.id || ''}`).toString();
          const safeName = baseName.replace(/[^a-zA-Z0-9._-]/g, '_');
          const finalName = `${task_id}-${safeName}`;
          const destPath = path.join(dest_dir, finalName);

          logger.info(`download_attachments: downloading ${url} -> ${destPath}`);

          const response = await axios({
            method: 'get',
            url,
            responseType: 'stream',
            headers: { 'Authorization': authHeader },
            timeout: 60000,
            maxRedirects: 5
          });

          await new Promise((resolve, reject) => {
            const writer = fs.createWriteStream(destPath);
            response.data.pipe(writer);
            writer.on('finish', resolve);
            writer.on('error', reject);
          });

          savedPaths.push(destPath);
        }

        logger.info(`download_attachments: success task_id=${task_id} count=${savedPaths.length}`);
        return {
          content: [{
            type: 'text',
            text: `Downloaded ${savedPaths.length} attachment(s) for ${task_id} to ${dest_dir}:\n` + savedPaths.map(p => `- ${p}`).join('\n')
          }]
        };
      } catch (error) {
        logger.error(`download_attachments: error task_id=${task_id}`, { message: error.message, stack: error.stack, task_id, dest_dir, types });
        return {
          content: [{
            type: 'text',
            text: `Error downloading attachments for ${task_id}: ${error.message}`
          }]
        };
      }
    }
  );

}
