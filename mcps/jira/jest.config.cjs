/** @type {import('jest').Config} */
module.exports = {
  // Use node environment
  testEnvironment: 'node',
  
  // Transform ESM modules to CommonJS for testing
  transform: {
    '^.+\\.js$': 'babel-jest'
  },
  
  // Configure Jest to handle modules properly
  transformIgnorePatterns: [
    'node_modules/(?!(jira-client|dotenv|winston)/)'
  ],
  
  // Verbose output for debugging
  verbose: true
};
