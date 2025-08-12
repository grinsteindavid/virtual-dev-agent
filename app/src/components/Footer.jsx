import React from 'react';
import logger from '../utils/logger';

/**
 * Footer component for the application
 * @returns {React.Element} Rendered Footer component
 */
const Footer = () => {
  logger.debug('Rendering Footer component');
  
  return (
    <footer className="app-footer">
      <div className="container">
        <p>&copy; {new Date().getFullYear()} Virtual Developer Agent</p>
      </div>
    </footer>
  );
};

export default Footer;
