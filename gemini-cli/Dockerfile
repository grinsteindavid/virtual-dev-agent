# Use a lightweight Node.js image as the base
FROM node:20-slim

# Set the working directory inside the container
WORKDIR /app

# Install Gemini CLI globally
# This ensures the 'gemini' command is available
RUN npm install -g @google/gemini-cli

# Expose any ports if your plan involves a web server or similar (optional)
# For example, if your plan builds a web app that listens on port 3000
# EXPOSE 3000

# Command to run when the container starts.
# We'll override this with docker-compose to run with specific prompts.
CMD ["gemini"]