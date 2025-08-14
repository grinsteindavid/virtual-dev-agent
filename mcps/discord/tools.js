import axios from 'axios';
import { z } from 'zod';
import winston from 'winston';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

// Configure logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'discord-mcp.log' })
  ]
});

/**
 * Register Discord tools with the MCP server
 * @param {McpServer} server - The MCP server instance
 */
export function registerDiscordTools(server) {
  // Tool: Send Discord webhook message
  server.registerTool(
    'send_webhook_message',
    {
      title: 'Send Discord Webhook Message',
      description: 'Send a message to Discord via webhook',
      inputSchema: {
        content: z.string().describe('Message content to send'),
        username: z.string().optional().describe('Username to display (optional)'),
        avatar_url: z.string().optional().describe('Avatar URL to display (optional)')
      }
    },
    async ({ content, username, avatar_url }) => {
      logger.info('send_webhook_message: invoked', {
        contentLength: content?.length ?? 0,
        username,
        hasAvatarUrl: Boolean(avatar_url)
      });
      try {
        const webhookUrl = process.env.DISCORD_WEBHOOK_URL;

        if (!webhookUrl) {
          logger.error('send_webhook_message: error', { message: 'Discord webhook URL not configured' });
          return {
            content: [{
              type: 'text',
              text: 'Error: Discord webhook URL not configured'
            }]
          };
        }

        const payload = {
          content,
          ...(username && { username }),
          ...(avatar_url && { avatar_url })
        };

        const response = await axios.post(webhookUrl, payload, {
          headers: {
            'Content-Type': 'application/json'
          }
        });

        logger.info('send_webhook_message: success', { status: response.status });
        return {
          content: [{
            type: 'text',
            text: `Successfully sent message to Discord. Status: ${response.status}`
          }]
        };
      } catch (error) {
        logger.error('send_webhook_message: error', { message: error.message, stack: error.stack });
        return {
          content: [{
            type: 'text',
            text: `Error sending Discord message: ${error.message}`
          }]
        };
      }
    }
  );

  // Tool: Send Discord embed message
  server.registerTool(
    'send_embed_message',
    {
      title: 'Send Discord Embed Message',
      description: 'Send an embed message to Discord via webhook',
      inputSchema: {
        title: z.string().describe('Embed title'),
        description: z.string().describe('Embed description'),
        color: z.number().optional().describe('Embed color (decimal)'),
        url: z.string().optional().describe('Embed URL'),
        username: z.string().optional().describe('Username to display (optional)')
      }
    },
    async ({ title, description, color, url, username }) => {
      logger.info('send_embed_message: invoked', {
        title,
        hasUrl: Boolean(url),
        colorPresent: Boolean(color),
        username
      });
      try {
        const webhookUrl = process.env.DISCORD_WEBHOOK_URL;

        if (!webhookUrl) {
          return {
            content: [{
              type: 'text',
              text: 'Error: Discord webhook URL not configured'
            }]
          };
        }

        const embed = {
          title,
          description,
          ...(color && { color }),
          ...(url && { url }),
          timestamp: new Date().toISOString()
        };

        const payload = {
          embeds: [embed],
          ...(username && { username })
        };

        const response = await axios.post(webhookUrl, payload, {
          headers: {
            'Content-Type': 'application/json'
          }
        });

        logger.info('send_embed_message: success', { status: response.status });
        return {
          content: [{
            type: 'text',
            text: `Successfully sent embed message to Discord. Status: ${response.status}`
          }]
        };
      } catch (error) {
        logger.error('send_embed_message: error', { message: error.message, stack: error.stack });
        return {
          content: [{
            type: 'text',
            text: `Error sending Discord embed: ${error.message}`
          }]
        };
      }
    }
  );

  // Tool: Send notification message
  server.registerTool(
    'send_notification',
    {
      title: 'Send Discord Notification',
      description: 'Send a formatted notification message to Discord',
      inputSchema: {
        type: z.enum(['info', 'success', 'warning', 'error']).describe('Notification type'),
        message: z.string().describe('Notification message'),
        details: z.string().optional().describe('Additional details (optional)')
      }
    },
    async ({ type, message, details }) => {
      logger.info('send_notification: invoked', {
        type,
        messageLength: message?.length ?? 0,
        hasDetails: Boolean(details)
      });
      try {
        const webhookUrl = process.env.DISCORD_WEBHOOK_URL;

        if (!webhookUrl) {
          return {
            content: [{
              type: 'text',
              text: 'Error: Discord webhook URL not configured'
            }]
          };
        }

        const colors = {
          info: 0x3498db,    // Blue
          success: 0x2ecc71, // Green
          warning: 0xf39c12, // Orange
          error: 0xe74c3c    // Red
        };

        const icons = {
          info: 'ℹ️',
          success: '✅',
          warning: '⚠️',
          error: '❌'
        };

        const embed = {
          title: `${icons[type]} ${type.charAt(0).toUpperCase() + type.slice(1)} Notification`,
          description: message,
          color: colors[type],
          timestamp: new Date().toISOString(),
          ...(details && {
            fields: [{
              name: 'Details',
              value: details,
              inline: false
            }]
          })
        };

        const payload = {
          embeds: [embed],
          username: 'Virtual Dev Agent'
        };

        const response = await axios.post(webhookUrl, payload, {
          headers: {
            'Content-Type': 'application/json'
          }
        });

        logger.info('send_notification: success', { status: response.status, type });
        return {
          content: [{
            type: 'text',
            text: `Successfully sent ${type} notification to Discord. Status: ${response.status}`
          }]
        };
      } catch (error) {
        logger.error('send_notification: error', { message: error.message, stack: error.stack });
        return {
          content: [{
            type: 'text',
            text: `Error sending Discord notification: ${error.message}`
          }]
        };
      }
    }
  );
}
