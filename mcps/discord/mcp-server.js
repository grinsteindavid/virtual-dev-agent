#!/usr/bin/env node

import express from 'express';
import { randomUUID } from 'crypto';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import axios from 'axios';
import { z } from 'zod';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config({ path: '../../.env' });

// Initialize Express app
const app = express();
app.use(express.json());

// Health check route
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', service: 'discord-mcp' });
});

// Create MCP server instance
const server = new McpServer({
  name: 'discord-mcp',
  version: '1.0.0'
});

// Register Discord tools

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

// Store active sessions
const sessions = new Map();

// Session management functions
const sessionIdGenerator = () => randomUUID();

const onSessionInitialized = (sessionId, transport) => {
  console.log(`New session initialized: ${sessionId}`);
  sessions.set(sessionId, { transport, createdAt: new Date() });
};

// Create transport with automatic session ID management
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator,
  onSessionInitialized
});

// Handle POST requests for JSON-RPC
app.post('/mcp', async (req, res) => {
  try {
    // The transport will automatically handle session IDs
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.error('Error handling MCP request:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// Handle GET requests for SSE streaming
app.get('/mcp', async (req, res) => {
  try {
    await transport.handleRequest(req, res);
  } catch (error) {
    console.error('Error handling SSE request:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// Handle DELETE requests to end sessions
app.delete('/mcp', async (req, res) => {
  try {
    await transport.handleRequest(req, res);
  } catch (error) {
    console.error('Error handling session deletion:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});


// Start the HTTP MCP server
async function main() {
  const port = process.env.PORT || 3001;
  
  // Connect the transport to the MCP server
  await server.connect(transport);
  
  // Start Express server
  app.listen(port, () => {
    console.log(`Discord MCP server listening on http://localhost:${port}`);
  });
}

main().catch((error) => {
  console.error('Failed to start Discord MCP server:', error);
  process.exit(1);
});
