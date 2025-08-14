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

  // Tool: Create pull request comment
  server.registerTool(
    'create_pull_request_comment',
    {
      title: 'Create GitHub Pull Request Comment',
      description: 'Add a comment to an existing pull request',
      inputSchema: {
        owner: z.string().describe('Repository owner/organization'),
        repo: z.string().describe('Repository name'),
        pull_number: z.number().describe('Pull request number'),
        body: z.string().describe('Comment text content'),
        commit_id: z.string().optional().describe('The SHA of the commit to comment on'),
        path: z.string().optional().describe('The relative path to the file to comment on'),
        line: z.number().optional().describe('The line index in the diff to comment on')
      }
    },
    async ({ owner, repo, pull_number, body, commit_id, path, line }) => {
      logger.info('create_pull_request_comment: invoked', { owner, repo, pull_number, hasBody: Boolean(body) });
      try {
        // If commit_id, path, and line are provided, create a review comment
        if (commit_id && path && line) {
          const { data } = await octokit.rest.pulls.createReviewComment({
            owner,
            repo,
            pull_number,
            body,
            commit_id,
            path,
            line
          });
          logger.info('create_pull_request_comment: created review comment', { id: data.id, url: data.html_url });
          return {
            content: [{
              type: 'text',
              text: `Successfully added review comment to PR #${pull_number} at ${path}:${line}\n` +
                    `Comment ID: ${data.id}\n` +
                    `URL: ${data.html_url}`
            }]
          };
        } else {
          // Otherwise create a regular issue comment (PRs are issues in GitHub's API)
          const { data } = await octokit.rest.issues.createComment({
            owner,
            repo,
            issue_number: pull_number,
            body
          });
          logger.info('create_pull_request_comment: created comment', { id: data.id, url: data.html_url });
          return {
            content: [{
              type: 'text',
              text: `Successfully added comment to PR #${pull_number}\n` +
                    `Comment ID: ${data.id}\n` +
                    `URL: ${data.html_url}`
            }]
          };
        }
      } catch (error) {
        logger.error('create_pull_request_comment: error', { message: error.message, stack: error.stack, owner, repo, pull_number });
        return {
          content: [{
            type: 'text',
            text: `Error creating pull request comment: ${error.message}`
          }]
        };
      }
    }
  );

  // Tool: List pull requests
  server.registerTool(
    'list_pull_requests',
    {
      title: 'List GitHub Pull Requests',
      description: 'List pull requests in a GitHub repository',
      inputSchema: {
        owner: z.string().describe('Repository owner/organization'),
        repo: z.string().describe('Repository name'),
        state: z.string().optional().default('open').describe('Pull request state (open, closed, all)'),
        limit: z.number().optional().default(10).describe('Maximum number of pull requests to return'),
        sort: z.string().optional().default('created').describe('Sort field (created, updated, popularity, long-running)'),
        direction: z.string().optional().default('desc').describe('Sort direction (asc, desc)')
      }
    },
    async ({ owner, repo, state = 'open', limit = 10, sort = 'created', direction = 'desc' }) => {
      logger.info('list_pull_requests: invoked', { owner, repo, state, limit, sort, direction });
      try {
        const { data } = await octokit.rest.pulls.list({
          owner,
          repo,
          state,
          per_page: limit,
          sort,
          direction
        });

        const prs = data.map(pr => ({
          number: pr.number,
          title: pr.title,
          state: pr.state,
          author: pr.user.login,
          created: pr.created_at,
          updated: pr.updated_at,
          head: pr.head.ref,
          base: pr.base.ref,
          url: pr.html_url
        }));
        logger.info('list_pull_requests: success', { count: prs.length, owner, repo, state });
        return {
          content: [{
            type: 'text',
            text: `Found ${prs.length} pull requests in ${owner}/${repo}:\n\n` +
                  prs.map(pr => 
                    `#${pr.number}: ${pr.title}\n` +
                    `  State: ${pr.state}\n` +
                    `  Author: ${pr.author}\n` +
                    `  Created: ${pr.created}\n` +
                    `  Updated: ${pr.updated}\n` +
                    `  Branch: ${pr.head} → ${pr.base}\n` +
                    `  URL: ${pr.url}\n`
                  ).join('\n')
          }]
        };
      } catch (error) {
        logger.error('list_pull_requests: error', { message: error.message, stack: error.stack, owner, repo });
        return {
          content: [{
            type: 'text',
            text: `Error listing pull requests: ${error.message}`
          }]
        };
      }
    }
  );
}
