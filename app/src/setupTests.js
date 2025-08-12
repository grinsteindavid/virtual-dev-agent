// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Suppress React Testing Library warnings about ReactDOMTestUtils.act deprecation
const originalError = console.error;
console.error = (...args) => {
  if (
    args[0]?.includes('Warning: `ReactDOMTestUtils.act` is deprecated') ||
    args[0]?.includes('https://react.dev/warnings/react-dom-test-utils')
  ) {
    return; // Suppress the specific warning
  }
  originalError(...args); // Keep other console errors
};

// You can add more global test setup here if needed
