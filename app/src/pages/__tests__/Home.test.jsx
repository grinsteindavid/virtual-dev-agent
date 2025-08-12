import React from 'react';
import { render, screen } from '@testing-library/react';
import Home from '../Home';

// Mock the logger to prevent console output during tests
jest.mock('../../utils/logger', () => ({
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
}));

describe('Home Page', () => {
  beforeEach(() => {
    // Setup before each test
  });

  afterEach(() => {
    // Cleanup after each test
    jest.clearAllMocks();
  });

  test('should render welcome heading', () => {
    // Arrange
    render(<Home />);
    
    // Act - rendering is the action
    
    // Assert
    expect(screen.getByText('Welcome to the React Boilerplate')).toBeInTheDocument();
  });

  test('should render feature list', () => {
    // Arrange
    render(<Home />);
    
    // Act - rendering is the action
    
    // Assert
    expect(screen.getByText('React Router for navigation')).toBeInTheDocument();
    expect(screen.getByText('Comprehensive logging system')).toBeInTheDocument();
    expect(screen.getByText('Jest testing configuration')).toBeInTheDocument();
    expect(screen.getByText('Component structure following best practices')).toBeInTheDocument();
  });

  test('should render description about Virtual Developer Agent', () => {
    // Arrange
    render(<Home />);
    
    // Act - rendering is the action
    
    // Assert
    expect(screen.getByText(/The Virtual Developer Agent will use this boilerplate/i)).toBeInTheDocument();
  });
});
