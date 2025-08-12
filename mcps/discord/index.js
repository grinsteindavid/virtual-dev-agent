const { Client, GatewayIntentBits, Events } = require('discord.js');
const winston = require('winston');
const express = require('express');
const dotenv = require('dotenv');
const cors = require('cors');

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
    new winston.transports.File({ filename: 'discord-mcp.log' })
  ]
});

// Initialize Discord client
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

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
    description: 'Discord integration for sending and receiving messages',
    functions: [
      {
        name: 'send_message',
        description: 'Send a message to a Discord channel',
        parameters: {
          type: 'object',
          properties: {
            channelId: {
              type: 'string',
              description: 'The Discord channel ID to send the message to'
            },
            message: {
              type: 'string',
              description: 'The message content to send'
            }
          },
          required: ['channelId', 'message']
        }
      }
    ]
  };
  
  res.json(toolSchema);
});

// API endpoint to send messages to Discord
app.post('/api/send-message', async (req, res) => {
  try {
    const { channelId, message } = req.body;
    
    if (!channelId || !message) {
      return res.status(400).json({ error: 'Missing channelId or message' });
    }
    
    const channel = await client.channels.fetch(channelId);
    if (!channel) {
      return res.status(404).json({ error: 'Channel not found' });
    }
    
    await channel.send(message);
    logger.info('Message sent to Discord', { channelId, message });
    
    return res.status(200).json({ success: true });
  } catch (error) {
    logger.error('Error sending message to Discord', { error: error.message });
    return res.status(500).json({ error: error.message });
  }
});

// API endpoint to get status updates
app.get('/api/status', (req, res) => {
  const isConnected = client.isReady();
  return res.status(200).json({ 
    status: isConnected ? 'connected' : 'disconnected',
    uptime: isConnected ? client.uptime : 0
  });
});

// Discord client events
client.once(Events.ClientReady, () => {
  logger.info('Discord bot is ready', { username: client.user.tag });
});

client.on(Events.MessageCreate, async (message) => {
  // Ignore messages from bots
  if (message.author.bot) return;
  
  // Log received messages
  logger.info('Message received', { 
    author: message.author.tag,
    content: message.content,
    channelId: message.channelId
  });
  
  // Process commands or mentions
  if (message.mentions.has(client.user)) {
    logger.info('Bot mentioned', { 
      author: message.author.tag,
      content: message.content
    });
    
    // Respond to mentions
    await message.reply('Virtual Developer Agent is listening. How can I help?');
  }
});

// Start the server and connect to Discord
async function start() {
  try {
    // Start API server
    app.listen(PORT, () => {
      logger.info(`Discord MCP server listening on port ${PORT}`);
      logger.info(`SSE endpoint available at http://localhost:${PORT}/sse`);
    });
    
    // Login to Discord
    await client.login(process.env.DISCORD_TOKEN);
  } catch (error) {
    logger.error('Failed to start Discord MCP', { error: error.message });
    process.exit(1);
  }
}

start();
