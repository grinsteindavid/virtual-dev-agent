FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install curl for healthchecks
RUN apk --no-cache add curl

# Copy package files and install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source code
COPY . .

# Set environment variables
ENV NODE_ENV=production

# Start the Jira MCP service
CMD ["node", "index.js"]
