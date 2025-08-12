const { Octokit } = require('@octokit/rest');
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

// Start the server
app.listen(PORT, () => {
  logger.info(`GitHub MCP API server listening on port ${PORT}`);
});
