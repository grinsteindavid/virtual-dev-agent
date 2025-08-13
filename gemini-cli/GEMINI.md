# Gemini CLI Guidelines

This document provides guidelines for the Gemini CLI when working with the Virtual Developer Agent. These instructions ensure consistent, high-quality code development when processing Jira tasks. Since the CLI runs in a Docker container with no user interaction, all processes must execute automatically without prompting for input.

## Core Principles

1. **Test-Driven Development**: Always write tests before implementing features
2. **Comprehensive Logging**: Include detailed logging for debugging and monitoring
3. **Code Quality**: Follow best practices for clean, maintainable code
4. **Documentation**: Document all code thoroughly
5. **Non-Interactive Execution**: All processes must run without requiring user input

## Project Setup

Always begin by checking that project dependencies are installed:

```bash
npm install
```

Only consider a task complete when all tests pass:

```bash
npm test -- --watchAll=false
```

## Testing Requirements

### Jest Test Files

For every Jira story/task, the virtual developer MUST:

1. Create dedicated Jest test files with the naming convention `*.test.js` or `*.spec.js`
2. Write tests that cover:
   - Happy path scenarios
   - Edge cases
   - Error handling
   - Component rendering (for UI components)
   - State management
   - API interactions (with mocks)

### Test Structure

Each test suite should follow this structure:

```javascript
describe('Component/Function Name', () => {
  beforeEach(() => {
    // Setup code
  });

  afterEach(() => {
    // Cleanup code
  });

  test('should perform expected behavior', () => {
    // Test implementation
    // Arrange
    // Act
    // Assert
  });
});
```

### Test Coverage

- Aim for at least 80% code coverage
- Test all public methods and functions
- Test component rendering and interactions
- Mock external dependencies

## Logging Requirements

### Log Levels

Use appropriate log levels:

- `error`: For errors that prevent normal operation
- `warn`: For potential issues that don't stop execution
- `info`: For significant events in normal operation
- `debug`: For detailed debugging information

### Logging Format

Include relevant context in logs:

```javascript
// Example logging
logger.info({
  action: 'userLogin',
  userId: user.id,
  timestamp: new Date().toISOString(),
  metadata: { browser, ip, location }
}, 'User successfully logged in');
```

### Log Points

Add logs at these critical points:

1. Function entry and exit
2. Before and after API calls
3. State changes
4. Error conditions
5. User interactions (for UI components)

## Code Implementation Process

1. **Analyze Requirements**: Understand the Jira story requirements
2. **Write Tests**: Create Jest test files based on requirements
3. **Implement Code**: Write the minimum code needed to pass tests
4. **Add Logging**: Implement comprehensive logging
5. **Run Tests**: Execute Jest tests until all pass
6. **Refactor**: Improve code quality while maintaining test coverage
7. **Document**: Add JSDoc comments and update documentation

## React Component Guidelines

### Component Structure

```javascript
// ComponentName.jsx
import React from 'react';
import PropTypes from 'prop-types';
import logger from '../utils/logger';

/**
 * ComponentName - Description of the component
 * @param {Object} props - Component props
 * @returns {React.Element} Rendered component
 */
const ComponentName = ({ prop1, prop2 }) => {
  logger.debug('Rendering ComponentName', { prop1, prop2 });
  
  // Component implementation
  
  return (
    <div className="component-name">
      {/* JSX content */}
    </div>
  );
};

ComponentName.propTypes = {
  prop1: PropTypes.string.isRequired,
  prop2: PropTypes.number,
};

ComponentName.defaultProps = {
  prop2: 0,
};

export default ComponentName;
```

### Test File Structure

```javascript
// ComponentName.test.jsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ComponentName from './ComponentName';

describe('ComponentName', () => {
  test('renders correctly with props', () => {
    render(<ComponentName prop1="test" prop2={42} />);
    expect(screen.getByText(/expected content/i)).toBeInTheDocument();
  });
  
  // Additional tests
});
```

## Execution Guidelines

When executing tasks in the non-interactive Docker environment, the virtual developer should:

1. Install dependencies automatically: `npm install --no-audit --no-fund --silent`
2. Run tests in CI mode: `npm test -- --watchAll=false --ci --silent`
3. Programmatically check test coverage
4. Automatically analyze test failures and apply fixes
5. Document all assumptions and decisions in code comments and logs
6. Verify all tests pass before code submission without user confirmation

## Reporting

After completing a task, automatically generate a report including:

1. Test coverage statistics
2. Passed/failed test counts
3. Implementation notes
4. Any known limitations or future improvements

This report should be programmatically added to the pull request description and automatically linked in the Jira ticket without requiring user intervention.

## Jira Workflow Guidelines

### Status Transitions

1. **Restricted Status Changes**: The virtual developer can only change Jira ticket status from "In Progress" to "In Review"
2. **Human-Only Status Changes**: All other status transitions (such as "To Do" to "In Progress" or "In Review" to "Done") must be performed by human team members
3. **Status Validation**: Before attempting to update a ticket status, verify that the current status is "In Progress" and the target status is "In Review"
4. **Error Handling**: Log appropriate warnings if status transition restrictions are encountered

### Comments Usage

1. **Limited Comment Posting**: Only add comments to Jira tickets after completing the assigned task
2. **Test Verification**: Comments should only be posted after verifying that all Jest test files have passed successfully
3. **Comment Content**: Comments should provide a concise summary of the work completed, including:
   - Key implementation details
   - Test coverage statistics
   - Any notable challenges or decisions made
4. **No Progress Updates**: Do not use comments for progress updates or intermediate status reports
5. **Cross-Platform Consistency**: The same comment summary must be sent to both Jira and Discord
   - Ensure identical content is shared across both platforms
   - Include relevant ticket IDs and PR links in both communications
