const JiraClient = require('jira-client');
const winston = require('winston');
const express = require('express');
const dotenv = require('dotenv');
const cors = require('cors');
const axios = require('axios');

// Load environment variables
dotenv.config({ path: '../../.env' });

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

// Initialize API server
const app = express();
const PORT = process.env.PORT || 3003;

app.use(express.json());
app.use(cors());

// SSE endpoint for gemini-cli MCP integration
app.get('/sse', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  
  // Send initial connection message
  res.write(`data: ${JSON.stringify({ type: 'connection', status: 'established' })}\n\n`);
  
  // Keep the connection alive with a ping every 30 seconds
  const pingInterval = setInterval(() => {
    res.write(`data: ${JSON.stringify({ type: 'ping', timestamp: Date.now() })}\n\n`);
  }, 30000);
  
  // Handle client disconnect
  req.on('close', () => {
    clearInterval(pingInterval);
    logger.info('SSE client disconnected');
  });
  
  logger.info('SSE client connected');
});

// MCP tool schema endpoint
app.get('/schema', (req, res) => {
  const toolSchema = {
    name: 'jira',
    description: 'Jira integration for task management',
    functions: [
      {
        name: 'get_task',
        description: 'Get details of a Jira task',
        parameters: {
          type: 'object',
          properties: {
            taskId: {
              type: 'string',
              description: 'The Jira task ID'
            }
          },
          required: ['taskId']
        }
      },
      {
        name: 'update_task_status',
        description: 'Update the status of a Jira task',
        parameters: {
          type: 'object',
          properties: {
            taskId: {
              type: 'string',
              description: 'The Jira task ID'
            },
            statusId: {
              type: 'string',
              description: 'The status ID to set'
            }
          },
          required: ['taskId', 'statusId']
        }
      },
      {
        name: 'add_comment',
        description: 'Add a comment to a Jira task',
        parameters: {
          type: 'object',
          properties: {
            taskId: {
              type: 'string',
              description: 'The Jira task ID'
            },
            comment: {
              type: 'string',
              description: 'Comment text to add'
            }
          },
          required: ['taskId', 'comment']
        }
      },
      {
        name: 'get_transitions',
        description: 'Get available transitions for a Jira task',
        parameters: {
          type: 'object',
          properties: {
            taskId: {
              type: 'string',
              description: 'The Jira task ID'
            }
          },
          required: ['taskId']
        }
      },
      {
        name: 'list_tasks',
        description: 'Get a list of Jira tasks',
        parameters: {
          type: 'object',
          properties: {
            status: {
              type: 'string',
              description: 'Filter tasks by status (e.g., "To Do", "In Progress")',
              default: 'To Do'
            },
            limit: {
              type: 'integer',
              description: 'Maximum number of tasks to return',
              default: 10
            }
          },
          required: []
        }
      }
    ]
  };
  
  res.json(toolSchema);
});

// API endpoint to get task details
app.get('/api/task/:taskId', async (req, res) => {
  try {
    const { taskId } = req.params;
    
    if (!taskId) {
      return res.status(400).json({ error: 'Missing taskId' });
    }
    
    const issue = await jira.findIssue(taskId);
    
    logger.info('Task details retrieved', { taskId });
    
    return res.status(200).json({
      id: issue.id,
      key: issue.key,
      summary: issue.fields.summary,
      description: issue.fields.description,
      status: issue.fields.status.name,
      assignee: issue.fields.assignee ? issue.fields.assignee.displayName : null,
      priority: issue.fields.priority ? issue.fields.priority.name : null,
      created: issue.fields.created,
      updated: issue.fields.updated
    });
  } catch (error) {
    logger.error('Error retrieving task details', { error: error.message });
    return res.status(500).json({ error: error.message });
  }
});

// API endpoint to update task status
app.post('/api/task/:taskId/status', async (req, res) => {
  try {
    const { taskId } = req.params;
    const { statusId } = req.body;
    
    if (!taskId || !statusId) {
      return res.status(400).json({ error: 'Missing taskId or statusId' });
    }
    
    // Use the proper Jira API method for transitions
    await jira.transitionIssue(taskId, {
      transition: {
        id: statusId
      }
    });
    
    logger.info('Task status updated', { taskId, statusId });
    
    return res.status(200).json({ success: true });
  } catch (error) {
    logger.error('Error updating task status', { error: error.message });
    return res.status(500).json({ error: error.message });
  }
});

// API endpoint to add a comment to a task
app.post('/api/task/:taskId/comment', async (req, res) => {
  try {
    const { taskId } = req.params;
    const { comment } = req.body;
    
    if (!taskId || !comment) {
      return res.status(400).json({ error: 'Missing taskId or comment' });
    }
    
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
    
    // Get authentication details from the jira client
    const auth = Buffer.from(`${process.env.JIRA_USERNAME}:${process.env.JIRA_API_TOKEN}`).toString('base64');
    
    // Use axios to directly call the Jira API with the ADF format
    const response = await axios.post(
      `https://${jiraUrl}/rest/api/3/issue/${taskId}/comment`,
      commentBody,
      {
        headers: {
          'Authorization': `Basic ${auth}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      }
    );
    
    logger.info('Comment added to task', { taskId });
    
    return res.status(200).json({ success: true, comment: response.data });
  } catch (error) {
    logger.error('Error adding comment to task', { error: error.message });
    return res.status(500).json({ error: error.message });
  }
});

// API endpoint to get available transitions for a task
app.get('/api/task/:taskId/transitions', async (req, res) => {
  try {
    const { taskId } = req.params;
    
    if (!taskId) {
      return res.status(400).json({ error: 'Missing taskId' });
    }
    
    const transitions = await jira.listTransitions(taskId);
    
    logger.info('Task transitions retrieved', { taskId });
    
    return res.status(200).json({
      transitions: transitions.transitions.map(transition => ({
        id: transition.id,
        name: transition.name,
        to: transition.to.name
      }))
    });
  } catch (error) {
    logger.error('Error retrieving task transitions', { error: error.message });
    return res.status(500).json({ error: error.message });
  }
});

// API endpoint to get available tasks
app.get('/api/tasks', async (req, res) => {
  try {
    const { status = 'To Do', limit = 10 } = req.query;
    
    const jql = `project = ${process.env.JIRA_PROJECT} AND status = "${status}" ORDER BY created DESC`;
    
    const issues = await jira.searchJira(jql, { maxResults: limit });
    
    logger.info('Tasks retrieved', { count: issues.issues.length });
    
    return res.status(200).json({
      total: issues.total,
      tasks: issues.issues.map(issue => ({
        id: issue.id,
        key: issue.key,
        summary: issue.fields.summary,
        status: issue.fields.status.name,
        assignee: issue.fields.assignee ? issue.fields.assignee.displayName : null,
        priority: issue.fields.priority ? issue.fields.priority.name : null
      }))
    });
  } catch (error) {
    logger.error('Error retrieving tasks', { error: error.message });
    return res.status(500).json({ error: error.message });
  }
});

// Health check endpoint for Docker
app.get('/health', (req, res) => {
  try {
    // For Docker health checks, always return healthy as long as the Express server is running
    // This prevents container restarts due to missing Jira credentials or other environment variables
    const credentialsStatus = {
      jiraUrl: process.env.JIRA_URL ? 'configured' : 'not configured',
      jiraUsername: process.env.JIRA_USERNAME ? 'configured' : 'not configured',
      jiraApiToken: process.env.JIRA_API_TOKEN ? 'configured' : 'not configured'
    };
    
    return res.status(200).json({ 
      status: 'healthy', 
      expressServer: 'running',
      credentials: credentialsStatus
    });
  } catch (error) {
    logger.error('Health check failed', { error: error.message });
    // Still return 200 to keep container running
    return res.status(200).json({ 
      status: 'healthy', 
      expressServer: 'running',
      error: error.message 
    });
  }
});

// Start the server
app.listen(PORT, () => {
  logger.info(`Jira MCP server listening on port ${PORT}`);
  logger.info(`SSE endpoint available at http://localhost:${PORT}/sse`);
});
