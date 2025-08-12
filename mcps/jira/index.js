const JiraClient = require('jira-client');
const winston = require('winston');
const express = require('express');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

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
const jira = new JiraClient({
  protocol: 'https',
  host: process.env.JIRA_URL,
  username: process.env.JIRA_USERNAME,
  password: process.env.JIRA_API_TOKEN,
  apiVersion: '3',
  strictSSL: true
});

// Initialize API server
const app = express();
const PORT = process.env.PORT || 3003;

app.use(express.json());

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
    
    await jira.updateIssue(taskId, {
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
    
    await jira.addComment(taskId, comment);
    
    logger.info('Comment added to task', { taskId });
    
    return res.status(200).json({ success: true });
  } catch (error) {
    logger.error('Error adding comment to task', { error: error.message });
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

// Start the server
app.listen(PORT, () => {
  logger.info(`Jira MCP API server listening on port ${PORT}`);
});
