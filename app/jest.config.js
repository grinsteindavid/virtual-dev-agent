module.exports = {
  // Setup files to run before each test
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
  
  // Transform JSX and ES modules
  transform: {
    '^.+.(js|jsx|ts|tsx)$': 'babel-jest',
  },
  
  // Ignore transformations for node_modules except for specific packages if needed
  transformIgnorePatterns: [
    '/node_modules/(?!react-router|react-router-dom).+.js$'
  ],
  
  // Test environment
  testEnvironment: 'jsdom',
  
  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/index.js',
    '!src/reportWebVitals.js'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  
  // Module name mapper for CSS and other non-JS files
  moduleNameMapper: {
    '.(css|less|scss|sass)$': '<rootDir>/src/__mocks__/styleMock.js',
    '.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$': '<rootDir>/src/__mocks__/fileMock.js'
  },
  
  // Roots for module resolution
  roots: ['<rootDir>/src']
};
