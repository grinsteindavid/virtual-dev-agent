import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Header from '../Header';

// Mock the logger to prevent console output during tests
jest.mock('../../utils/logger', () => {
  return {
    debug: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn()
  };
});

describe('Header Component', () => {
  beforeEach(() => {
    // Setup before each test
  });

  afterEach(() => {
    // Cleanup after each test
    jest.clearAllMocks();
  });

  test('should render with default title', () => {
    // Arrange
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    );
    
    // Act - rendering is the action
    
    // Assert
    expect(screen.getByText('React App')).toBeInTheDocument();
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('About')).toBeInTheDocument();
  });

  test('should render with custom title', () => {
    // Arrange
    const customTitle = 'Custom App Title';
    render(
      <BrowserRouter>
        <Header title={customTitle} />
      </BrowserRouter>
    );
    
    // Act - rendering is the action
    
    // Assert
    expect(screen.getByText(customTitle)).toBeInTheDocument();
  });

  test('should have navigation links', () => {
    // Arrange
    render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    );
    
    // Act - rendering is the action
    
    // Assert
    // Use getByRole to find links by their text content
    expect(screen.getByRole('link', { name: 'Home' })).toHaveAttribute('href', '/');
    expect(screen.getByRole('link', { name: 'About' })).toHaveAttribute('href', '/about');
  });
});
