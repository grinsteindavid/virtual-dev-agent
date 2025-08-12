import React from 'react';
import logger from '../utils/logger';

/**
 * About page component
 * @returns {React.Element} Rendered About page
 */
const About = () => {
  logger.info('Rendering About page');
  
  return (
    <div className="page about-page">
      <div className="container">
        <h2>About This Project</h2>
        <p>
          This React application is part of the Virtual Developer Agent project.
          The Virtual Developer Agent is a Docker Compose project that creates an
          automated virtual developer capable of handling tasks from Jira, reporting
          status to Discord, and creating pull requests in GitHub.
        </p>
        <h3>Architecture</h3>
        <p>
          The project is built using Docker Compose with multiple containerized services:
        </p>
        <ul>
          <li><strong>MCP Services</strong>: Message Control Program services that handle integration with external platforms</li>
          <li><strong>Gemini CLI</strong>: Command-line interface for the Gemini AI model that powers the virtual developer</li>
          <li><strong>React Boilerplate</strong>: This application, which serves as a foundation for development tasks</li>
        </ul>
        <h3>Development Process</h3>
        <p>
          When a new Jira task is assigned, the Virtual Developer Agent:
        </p>
        <ol>
          <li>Analyzes the task requirements using Gemini AI</li>
          <li>Creates Jest test files based on requirements</li>
          <li>Implements code with comprehensive logging</li>
          <li>Runs tests until they pass</li>
          <li>Creates a pull request via GitHub MCP</li>
          <li>Reports progress to Discord and updates Jira</li>
        </ol>
      </div>
    </div>
  );
};

export default About;
