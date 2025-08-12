const { Octokit } = require('@octokit/rest');
const winston = require('winston');
const express = require('express');
const dotenv = require('dotenv');
const cors = require('cors');

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
    new winston.transports.File({ filename: 'github-mcp.log' })
  ]
});

// Initialize GitHub client
const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN
});

// Initialize API server
const app = express();
const PORT = process.env.PORT || 3002;

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
    name: 'github',
    description: 'GitHub integration for repository management',
    functions: [
      {
        name: 'create_branch',
        description: 'Create a new branch in the repository',
        parameters: {
          type: 'object',
          properties: {
            branchName: {
              type: 'string',
              description: 'Name of the branch to create'
            },
            baseBranch: {
              type: 'string',
              description: 'Base branch to create from (default: main)'
            }
          },
          required: ['branchName']
        }
      },
      {
        name: 'create_pr',
        description: 'Create a pull request',
        parameters: {
          type: 'object',
          properties: {
            title: {
              type: 'string',
              description: 'Title of the pull request'
            },
            body: {
              type: 'string',
              description: 'Description of the pull request'
            },
            head: {
              type: 'string',
              description: 'Head branch name'
            },
            base: {
              type: 'string',
              description: 'Base branch name (default: main)'
            }
          },
          required: ['title', 'head']
        }
      }
    ]
  };
  
  res.json(toolSchema);
});

// API endpoint to create a branch
app.post('/api/create-branch', async (req, res) => {
  try {
    const { branchName, baseBranch = 'main' } = req.body;
    
    if (!branchName) {
      return res.status(400).json({ error: 'Missing branchName' });
    }
    
    const owner = process.env.GITHUB_OWNER;
    const repo = process.env.GITHUB_REPO;
    
    // Get the SHA of the base branch
    const { data: refData } = await octokit.git.getRef({
      owner,
      repo,
      ref: `heads/${baseBranch}`
    });
    
    // Create new branch
    await octokit.git.createRef({
      owner,
      repo,
      ref: `refs/heads/${branchName}`,
      sha: refData.object.sha
    });
    
    logger.info('Branch created', { owner, repo, branchName, baseBranch });
    
    return res.status(200).json({ 
      success: true,
      branch: branchName,
      sha: refData.object.sha
    });
  } catch (error) {
    logger.error('Error creating branch', { error: error.message });
    return res.status(500).json({ error: error.message });
  }
});

// API endpoint to create a pull request
app.post('/api/create-pr', async (req, res) => {
  try {
    const { title, body, head, base = 'main' } = req.body;
    
    if (!title || !head) {
      return res.status(400).json({ error: 'Missing required fields' });
    }
    
    const owner = process.env.GITHUB_OWNER;
    const repo = process.env.GITHUB_REPO;
    
    // Create pull request
    const { data: prData } = await octokit.pulls.create({
      owner,
      repo,
      title,
      body,
      head,
      base
    });
    
    logger.info('Pull request created', { 
      owner, 
      repo, 
      pr: prData.number,
      title,
      head,
      base
    });
    
    return res.status(200).json({ 
      success: true,
      pullRequestNumber: prData.number,
      url: prData.html_url
    });
  } catch (error) {
    logger.error('Error creating pull request', { error: error.message });
    return res.status(500).json({ error: error.message });
  }
});

// API endpoint to get repository status
app.get('/api/repo-status', async (req, res) => {
  try {
    const owner = process.env.GITHUB_OWNER;
    const repo = process.env.GITHUB_REPO;
    
    // Get repository information
    const { data: repoData } = await octokit.repos.get({
      owner,
      repo
    });
    
    // Get branches
    const { data: branchesData } = await octokit.repos.listBranches({
      owner,
      repo,
      per_page: 10
    });
    
    // Get pull requests
    const { data: prsData } = await octokit.pulls.list({
      owner,
      repo,
      state: 'open',
      per_page: 10
    });
    
    return res.status(200).json({
      repository: {
        name: repoData.name,
        description: repoData.description,
        defaultBranch: repoData.default_branch
      },
      branches: branchesData.map(branch => ({
        name: branch.name,
        protected: branch.protected
      })),
      pullRequests: prsData.map(pr => ({
        number: pr.number,
        title: pr.title,
        state: pr.state,
        url: pr.html_url
      }))
    });
  } catch (error) {
    logger.error('Error getting repository status', { error: error.message });
    return res.status(500).json({ error: error.message });
  }
});

// Health check endpoint for Docker
app.get('/health', (req, res) => {
  try {
    // For Docker health checks, always return healthy as long as the Express server is running
    // This prevents container restarts due to missing GitHub token or other environment variables
    return res.status(200).json({ 
      status: 'healthy', 
      expressServer: 'running',
      githubToken: process.env.GITHUB_TOKEN ? 'configured' : 'not configured'
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
  logger.info(`GitHub MCP server listening on port ${PORT}`);
  logger.info(`SSE endpoint available at http://localhost:${PORT}/sse`);
});
