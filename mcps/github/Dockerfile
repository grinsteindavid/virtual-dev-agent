FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install dependencies including git and curl for healthchecks
RUN apk add --no-cache git curl

# Copy package files and install dependencies
COPY package.json ./
RUN npm install

# Copy source code
COPY . .

# Set environment variables
ENV NODE_ENV=production

# Start the GitHub MCP service
CMD ["node", "mcp-server.js"]
