import React from 'react';
import logger from '../utils/logger';

/**
 * Home page component
 * @returns {React.Element} Rendered Home page
 */
const Home = () => {
  logger.info('Rendering Home page');
  
  return (
    <div className="page home-page">
      <div className="container">
        <h2>Welcome to the React Boilerplate</h2>
        <p>
          This is a starter template for React applications that will be managed by the Virtual Developer Agent.
          It includes:
        </p>
        <ul>
          <li>React Router for navigation</li>
          <li>Comprehensive logging system</li>
          <li>Jest testing configuration</li>
          <li>Component structure following best practices</li>
        </ul>
        <p>
          The Virtual Developer Agent will use this boilerplate as a foundation for implementing
          features based on Jira tasks.
        </p>
      </div>
    </div>
  );
};

export default Home;
