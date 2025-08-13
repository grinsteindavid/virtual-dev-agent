/** @type {import('jest').Config} */
export default {
  // Use node environment
  testEnvironment: 'node',
  
  // Transform ESM modules
  transform: {},
  
  // Modify how Jest resolves modules
  moduleNameMapper: {
    '^(\\.{1,2}/.*)\\.js$': '$1'
  },
  
  // Configure Jest to handle ESM properly
  transformIgnorePatterns: [
    'node_modules/(?!(jira-client|dotenv|winston)/)'
  ],
  
  // Verbose output for debugging
  verbose: true
};
