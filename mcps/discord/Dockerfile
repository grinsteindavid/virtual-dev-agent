FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install curl for healthchecks
RUN apk --no-cache add curl

# Install dependencies
COPY package.json ./
RUN npm install --no-optional && npm cache clean --force

# Copy source code
COPY . .

# Set environment variables
ENV NODE_ENV=production

# Start the Discord MCP service
CMD ["node", "index.js"]
