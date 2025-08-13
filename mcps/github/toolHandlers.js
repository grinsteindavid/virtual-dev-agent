import { Octokit } from '@octokit/rest';
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
    new winston.transports.File({ filename: 'github-mcp.log' })
  ]
});

// Load environment variables
dotenv.config({ path: '../../.env' });

// Initialize GitHub client
const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN
});

// Tool: Get repository information
export const getRepoInfoTool = {
  name: 'get_repo_info',
  config: {
    title: 'Get Repository Info',
    description: 'Get information about a GitHub repository',
    inputSchema: {
      owner: z.string().describe('Repository owner/organization'),
      repo: z.string().describe('Repository name')
    }
  },
  handler: async ({ owner, repo }) => {
    logger.info(`Executing get_repo_info tool for ${owner}/${repo}`);
    try {
      const { data } = await octokit.rest.repos.get({
        owner,
        repo
      });
      
      logger.info(`Successfully retrieved info for repository ${owner}/${repo}`);
      return {
        content: [{
          type: 'text',
          text: `Repository: ${data.full_name}\n` +
                `Description: ${data.description || 'No description'}\n` +
                `Language: ${data.language || 'Not specified'}\n` +
                `Stars: ${data.stargazers_count}\n` +
                `Forks: ${data.forks_count}\n` +
                `Open Issues: ${data.open_issues_count}\n` +
                `Created: ${data.created_at}\n` +
                `Updated: ${data.updated_at}\n` +
                `URL: ${data.html_url}`
        }]
      };
    } catch (error) {
      logger.error(`Error getting repository info for ${owner}/${repo}: ${error.message}`);
      return {
        content: [{
          type: 'text',
          text: `Error getting repository info: ${error.message}`
        }]
      };
    }
  }
};

// Tool: List issues
export const listIssuesTool = {
  name: 'list_issues',
  config: {
    title: 'List GitHub Issues',
    description: 'List issues in a GitHub repository',
    inputSchema: {
      owner: z.string().describe('Repository owner/organization'),
      repo: z.string().describe('Repository name'),
      state: z.string().optional().default('open').describe('Issue state (open, closed, all)'),
      limit: z.number().optional().default(10).describe('Maximum number of issues to return')
    }
  },
  handler: async ({ owner, repo, state = 'open', limit = 10 }) => {
    logger.info(`Executing list_issues tool for ${owner}/${repo} with state: ${state}, limit: ${limit}`);
    try {
      const { data } = await octokit.rest.issues.listForRepo({
        owner,
        repo,
        state,
        per_page: limit
      });
      
      const issues = data.map(issue => ({
        number: issue.number,
        title: issue.title,
        state: issue.state,
        author: issue.user.login,
        created: issue.created_at,
        url: issue.html_url
      }));
      
      logger.info(`Successfully listed ${issues.length} issues for ${owner}/${repo}`);
      return {
        content: [{
          type: 'text',
          text: `Found ${issues.length} issues in ${owner}/${repo}:\n\n` +
                issues.map(issue => 
                  `#${issue.number}: ${issue.title}\n` +
                  `  State: ${issue.state}\n` +
                  `  Author: ${issue.author}\n` +
                  `  Created: ${issue.created}\n` +
                  `  URL: ${issue.url}\n`
                ).join('\n')
        }]
      };
    } catch (error) {
      logger.error(`Error listing issues for ${owner}/${repo}: ${error.message}`);
      return {
        content: [{
          type: 'text',
          text: `Error listing issues: ${error.message}`
        }]
      };
    }
  }
};

// Tool: Create issue
export const createIssueTool = {
  name: 'create_issue',
  config: {
    title: 'Create GitHub Issue',
    description: 'Create a new issue in a GitHub repository',
    inputSchema: {
      owner: z.string().describe('Repository owner/organization'),
      repo: z.string().describe('Repository name'),
      title: z.string().describe('Issue title'),
      body: z.string().optional().describe('Issue body/description')
    }
  },
  handler: async ({ owner, repo, title, body }) => {
    logger.info(`Executing create_issue tool for ${owner}/${repo} with title: ${title}`);
    try {
      const { data } = await octokit.rest.issues.create({
        owner,
        repo,
        title,
        body
      });
      
      logger.info(`Successfully created issue #${data.number} in ${owner}/${repo}`);
      return {
        content: [{
          type: 'text',
          text: `Successfully created issue #${data.number}: ${data.title}\n` +
                `URL: ${data.html_url}`
        }]
      };
    } catch (error) {
      logger.error(`Error creating issue in ${owner}/${repo}: ${error.message}`);
      return {
        content: [{
          type: 'text',
          text: `Error creating issue: ${error.message}`
        }]
      };
    }
  }
};

// Tool: Create pull request
export const createPullRequestTool = {
  name: 'create_pull_request',
  config: {
    title: 'Create GitHub Pull Request',
    description: 'Create a new pull request in a GitHub repository',
    inputSchema: {
      owner: z.string().describe('Repository owner/organization'),
      repo: z.string().describe('Repository name'),
      title: z.string().describe('Pull request title'),
      body: z.string().optional().describe('Pull request body/description'),
      head: z.string().describe('Branch to merge from (source branch)'),
      base: z.string().optional().default('main').describe('Branch to merge into (target branch, default: main)')
    }
  },
  handler: async ({ owner, repo, title, body, head, base = 'main' }) => {
    logger.info(`Executing create_pull_request tool for ${owner}/${repo} from ${head} to ${base}`);
    try {
      const { data } = await octokit.rest.pulls.create({
        owner,
        repo,
        title,
        body,
        head,
        base
      });
      
      logger.info(`Successfully created pull request #${data.number} in ${owner}/${repo}`);
      return {
        content: [{
          type: 'text',
          text: `Successfully created pull request #${data.number}: ${data.title}\n` +
                `From: ${data.head.ref} → ${data.base.ref}\n` +
                `State: ${data.state}\n` +
                `URL: ${data.html_url}`
        }]
      };
    } catch (error) {
      logger.error(`Error creating pull request in ${owner}/${repo}: ${error.message}`);
      return {
        content: [{
          type: 'text',
          text: `Error creating pull request: ${error.message}`
        }]
      };
    }
  }
};

// Export all tools as an array for easy registration
export const tools = [
  getRepoInfoTool,
  listIssuesTool,
  createIssueTool,
  createPullRequestTool
];

// Export octokit client for potential use in tests
export { octokit };
