import { z } from 'zod';
import winston from 'winston';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { Octokit } from '@octokit/rest';

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

/**
 * Register GitHub tools with the MCP server
 * @param {McpServer} server - The MCP server instance
 * @param {Octokit} octokit - Initialized Octokit client
 */
export function registerGithubTools(server, octokit) {
  // Tool: Get repository information
  server.registerTool(
    'get_repo_info',
    {
      title: 'Get Repository Info',
      description: 'Get information about a GitHub repository',
      inputSchema: {
        owner: z.string().describe('Repository owner/organization'),
        repo: z.string().describe('Repository name')
      }
    },
    async ({ owner, repo }) => {
      logger.info('get_repo_info: invoked', { owner, repo });
      try {
        const { data } = await octokit.rest.repos.get({
          owner,
          repo
        });
        logger.info('get_repo_info: success', { full_name: data.full_name, stars: data.stargazers_count });
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
        logger.error('get_repo_info: error', { message: error.message, stack: error.stack, owner, repo });
        return {
          content: [{
            type: 'text',
            text: `Error getting repository info: ${error.message}`
          }]
        };
      }
    }
  );

  // Tool: List issues
  server.registerTool(
    'list_issues',
    {
      title: 'List GitHub Issues',
      description: 'List issues in a GitHub repository',
      inputSchema: {
        owner: z.string().describe('Repository owner/organization'),
        repo: z.string().describe('Repository name'),
        state: z.string().optional().default('open').describe('Issue state (open, closed, all)'),
        limit: z.number().optional().default(10).describe('Maximum number of issues to return')
      }
    },
    async ({ owner, repo, state = 'open', limit = 10 }) => {
      logger.info('list_issues: invoked', { owner, repo, state, limit });
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
        logger.info('list_issues: success', { count: issues.length, owner, repo, state });
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
        logger.error('list_issues: error', { message: error.message, stack: error.stack, owner, repo });
        return {
          content: [{
            type: 'text',
            text: `Error listing issues: ${error.message}`
          }]
        };
      }
    }
  );

  // Tool: Create issue
  server.registerTool(
    'create_issue',
    {
      title: 'Create GitHub Issue',
      description: 'Create a new issue in a GitHub repository',
      inputSchema: {
        owner: z.string().describe('Repository owner/organization'),
        repo: z.string().describe('Repository name'),
        title: z.string().describe('Issue title'),
        body: z.string().optional().describe('Issue body/description')
      }
    },
    async ({ owner, repo, title, body }) => {
      logger.info('create_issue: invoked', { owner, repo, title, hasBody: Boolean(body) });
      try {
        const { data } = await octokit.rest.issues.create({
          owner,
          repo,
          title,
          body
        });
        logger.info('create_issue: success', { number: data.number, url: data.html_url, owner, repo });
        return {
          content: [{
            type: 'text',
            text: `Successfully created issue #${data.number}: ${data.title}\n` +
                  `URL: ${data.html_url}`
          }]
        };
      } catch (error) {
        logger.error('create_issue: error', { message: error.message, stack: error.stack, owner, repo });
        return {
          content: [{
            type: 'text',
            text: `Error creating issue: ${error.message}`
          }]
        };
      }
    }
  );

  // Tool: Create pull request
  server.registerTool(
    'create_pull_request',
    {
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
    async ({ owner, repo, title, body, head, base = 'main' }) => {
      logger.info('create_pull_request: invoked', { owner, repo, title, head, base, hasBody: Boolean(body) });
      try {
        const { data } = await octokit.rest.pulls.create({
          owner,
          repo,
          title,
          body,
          head,
          base
        });
        logger.info('create_pull_request: success', { number: data.number, url: data.html_url, head: data.head?.ref, base: data.base?.ref });
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
        logger.error('create_pull_request: error', { message: error.message, stack: error.stack, owner, repo, head, base });
        return {
          content: [{
            type: 'text',
            text: `Error creating pull request: ${error.message}`
          }]
        };
      }
    }
  );
}
