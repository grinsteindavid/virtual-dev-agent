import React from 'react';
import { Link } from 'react-router-dom';
import logger from '../utils/logger';

/**
 * NotFound page component for 404 errors
 * @returns {React.Element} Rendered NotFound page
 */
const NotFound = () => {
  logger.warn('Rendering NotFound page - user attempted to access non-existent route');
  
  return (
    <div className="page not-found-page">
      <div className="container">
        <h2>404 - Page Not Found</h2>
        <p>The page you are looking for does not exist.</p>
        <p>
          <Link to="/">Return to Home</Link>
        </p>
      </div>
    </div>
  );
};

export default NotFound;
