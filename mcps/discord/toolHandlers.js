import axios from 'axios';
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
    new winston.transports.File({ filename: 'discord-mcp.log' })
  ]
});

// Load environment variables
dotenv.config({ path: '../../.env' });

// Tool: Send Discord webhook message
export const sendWebhookMessageTool = {
  name: 'send_webhook_message',
  config: {
    title: 'Send Discord Webhook Message',
    description: 'Send a message to Discord via webhook',
    inputSchema: {
      content: z.string().describe('Message content to send'),
      username: z.string().optional().describe('Username to display (optional)'),
      avatar_url: z.string().optional().describe('Avatar URL to display (optional)')
    }
  },
  handler: async ({ content, username, avatar_url }) => {
    logger.info('Executing send_webhook_message tool');
    try {
      const webhookUrl = process.env.DISCORD_WEBHOOK_URL;
      
      if (!webhookUrl) {
        logger.error('Discord webhook URL not configured');
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

      logger.info(`Successfully sent message to Discord. Status: ${response.status}`);
      return {
        content: [{
          type: 'text',
          text: `Successfully sent message to Discord. Status: ${response.status}`
        }]
      };
    } catch (error) {
      logger.error(`Error sending Discord message: ${error.message}`);
      return {
        content: [{
          type: 'text',
          text: `Error sending Discord message: ${error.message}`
        }]
      };
    }
  }
};

// Tool: Send Discord embed message
export const sendEmbedMessageTool = {
  name: 'send_embed_message',
  config: {
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
  handler: async ({ title, description, color, url, username }) => {
    logger.info('Executing send_embed_message tool');
    try {
      const webhookUrl = process.env.DISCORD_WEBHOOK_URL;
      
      if (!webhookUrl) {
        logger.error('Discord webhook URL not configured');
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

      logger.info(`Successfully sent embed message to Discord. Status: ${response.status}`);
      return {
        content: [{
          type: 'text',
          text: `Successfully sent embed message to Discord. Status: ${response.status}`
        }]
      };
    } catch (error) {
      logger.error(`Error sending Discord embed: ${error.message}`);
      return {
        content: [{
          type: 'text',
          text: `Error sending Discord embed: ${error.message}`
        }]
      };
    }
  }
};

// Tool: Send notification message
export const sendNotificationTool = {
  name: 'send_notification',
  config: {
    title: 'Send Discord Notification',
    description: 'Send a formatted notification message to Discord',
    inputSchema: {
      type: z.enum(['info', 'success', 'warning', 'error']).describe('Notification type'),
      message: z.string().describe('Notification message'),
      details: z.string().optional().describe('Additional details (optional)')
    }
  },
  handler: async ({ type, message, details }) => {
    logger.info(`Executing send_notification tool with type: ${type}`);
    try {
      const webhookUrl = process.env.DISCORD_WEBHOOK_URL;
      
      if (!webhookUrl) {
        logger.error('Discord webhook URL not configured');
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

      logger.info(`Successfully sent ${type} notification to Discord. Status: ${response.status}`);
      return {
        content: [{
          type: 'text',
          text: `Successfully sent ${type} notification to Discord. Status: ${response.status}`
        }]
      };
    } catch (error) {
      logger.error(`Error sending Discord notification: ${error.message}`);
      return {
        content: [{
          type: 'text',
          text: `Error sending Discord notification: ${error.message}`
        }]
      };
    }
  }
};

// Export all tools as an array for easy registration
export const tools = [
  sendWebhookMessageTool,
  sendEmbedMessageTool,
  sendNotificationTool
];
