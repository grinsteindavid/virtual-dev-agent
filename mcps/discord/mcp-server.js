#!/usr/bin/env node

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import axios from 'axios';
import { z } from 'zod';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config({ path: '../../.env' });

// Create MCP server instance
const server = new McpServer({
  name: 'discord-mcp',
  version: '1.0.0'
});

// Register Discord tools

// Tool: Send Discord webhook message
server.tool(
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

      return {
        content: [{
          type: 'text',
          text: `Successfully sent message to Discord. Status: ${response.status}`
        }]
      };
    } catch (error) {
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
server.tool(
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

      return {
        content: [{
          type: 'text',
          text: `Successfully sent embed message to Discord. Status: ${response.status}`
        }]
      };
    } catch (error) {
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
server.tool(
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

      return {
        content: [{
          type: 'text',
          text: `Successfully sent ${type} notification to Discord. Status: ${response.status}`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error sending Discord notification: ${error.message}`
        }]
      };
    }
  }
);

// Start the STDIO MCP server
async function main() {
  // Create STDIO transport
  const transport = new StdioServerTransport();
  
  // Connect the server to the transport
  await server.connect(transport);
  
  console.error('Discord MCP server started with STDIO transport');
}

main().catch((error) => {
  console.error('Failed to start Discord MCP server:', error);
  process.exit(1);
});
