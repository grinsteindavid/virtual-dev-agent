const express = require('express');
const axios = require('axios');
const winston = require('winston');
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
    new winston.transports.File({ filename: 'discord-mcp.log' })
  ]
});

// No Discord client initialization needed for webhook implementation

// Initialize API server
const app = express();
const PORT = process.env.PORT || 3001;

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
    name: 'discord',
    description: 'Discord integration for sending messages via webhook',
    functions: [
      {
        name: 'send_message',
        description: 'Send a message to a Discord channel via webhook',
        parameters: {
          type: 'object',
          properties: {
            message: {
              type: 'string',
              description: 'The message content to send'
            },
            title: {
              type: 'string',
              description: 'Optional: Title for the message'
            }
          },
          required: ['message']
        }
      }
    ]
  };
  
  res.json(toolSchema);
});

// API endpoint to send messages to Discord via webhook
app.post('/api/send-message', async (req, res) => {
  try {
    const { message, title } = req.body;
    const webhookUrl = process.env.DISCORD_WEBHOOK_URL;
    
    if (!webhookUrl) {
      return res.status(500).json({ error: 'Discord webhook URL not configured' });
    }
    
    if (!message) {
      return res.status(400).json({ error: 'Missing message content' });
    }
    
    const payload = {
      content: message
    };
    
    // Add title as embed if provided
    if (title) {
      payload.embeds = [{
        title: title
      }];
    }
    
    await axios.post(webhookUrl, payload);
    logger.info('Message sent to Discord webhook', { message, title });
    
    return res.status(200).json({ success: true });
  } catch (error) {
    logger.error('Error sending message to Discord webhook', { error: error.message });
    return res.status(500).json({ error: error.message });
  }
});

// API endpoint to get status updates
app.get('/api/status', (req, res) => {
  return res.status(200).json({ 
    status: 'ready',
    webhookConfigured: !!process.env.DISCORD_WEBHOOK_URL
  });
});

// Health check endpoint for Docker
app.get('/health', (req, res) => {
  // For Docker health checks, always return healthy as long as the Express server is running
  return res.status(200).json({ 
    status: 'healthy', 
    expressServer: 'running',
    webhookConfigured: !!process.env.DISCORD_WEBHOOK_URL
  });
});

// No Discord client events needed for webhook implementation

// Start the server
function start() {
  try {
    // Start API server
    app.listen(PORT, () => {
      logger.info(`Discord Webhook MCP server listening on port ${PORT}`);
      logger.info(`SSE endpoint available at http://localhost:${PORT}/sse`);
      
      if (!process.env.DISCORD_WEBHOOK_URL) {
        logger.warn('DISCORD_WEBHOOK_URL environment variable not set');
      }
    });
  } catch (error) {
    logger.error('Failed to start Discord Webhook MCP', { error: error.message });
    process.exit(1);
  }
}

start();
