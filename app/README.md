# React Boilerplate for Virtual Developer Agent

This React application serves as a boilerplate for the Virtual Developer Agent to use when implementing features based on Jira tasks.

## Project Structure

```
boilerplate/
├── public/               # Static files
├── src/                  # Source code
│   ├── components/       # Reusable components
│   │   └── __tests__/    # Component tests
│   ├── pages/            # Page components
│   │   └── __tests__/    # Page tests
│   ├── utils/            # Utility functions
│   ├── App.js            # Main App component
│   ├── App.css           # App styles
│   ├── index.js          # Entry point
│   └── index.css         # Global styles
├── package.json          # Dependencies and scripts
└── README.md             # This file
```

## Development Guidelines

### Component Structure

- Each component should be in its own file
- Components should be focused and follow the single responsibility principle
- Use JSX for component definition
- Include PropTypes for all props
- Use functional components with hooks

### Testing

- Every component must have corresponding test files in the `__tests__` directory
- Tests should follow the Arrange-Act-Assert pattern
- Mock external dependencies
- Aim for high test coverage (minimum 80%)

### Logging

- Use the provided logger utility for all logging
- Include appropriate log levels (debug, info, warn, error)
- Log component rendering and important state changes

## Available Scripts

- `npm start`: Run the development server
- `npm test`: Run tests
- `npm run build`: Build for production
- `npm run lint`: Run linting
- `npm run format`: Format code with Prettier

## Integration with Virtual Developer Agent

This boilerplate is designed to be used by the Virtual Developer Agent, which will:

1. Analyze Jira tasks
2. Create Jest test files based on requirements
3. Implement components and features
4. Ensure all tests pass
5. Create pull requests via GitHub

For more details, refer to the main project README and the gemini-guidelines.md file.
