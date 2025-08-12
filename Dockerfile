FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install dependencies for development environment
RUN apk add --no-cache \
    git \
    bash \
    curl \
    python3 \
    py3-pip \
    jq

# Install global npm packages
RUN npm install -g \
    jest \
    eslint \
    prettier \
    typescript \
    ts-node

# Copy boilerplate package.json and install dependencies
COPY ./boilerplate/package.json* ./boilerplate/package-lock.json* ./
RUN npm ci

# Copy gemini guidelines
COPY ./gemini-guidelines.md /guidelines.md

# Create a script to handle tasks
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set environment variables
ENV NODE_ENV=development
ENV PATH="/app/node_modules/.bin:${PATH}"

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
