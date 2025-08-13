# Use a lightweight Node.js image as the base
FROM node:22-slim

# Set the working directory inside the container
WORKDIR /app

# Install essential development tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    jq \
    zip \
    unzip \
    python3 \
    python3-pip \
    build-essential \
    procps \
    --no-install-recommends

# Install Gemini CLI globally
# This ensures the 'gemini' command is available
RUN npm install -g @google/gemini-cli

# Command to run when the container starts.
# We'll override this with docker-compose to run with specific prompts.
CMD ["gemini"]