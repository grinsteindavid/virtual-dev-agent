import React from 'react';
import { Link } from 'react-router-dom';
import PropTypes from 'prop-types';
import logger from '../utils/logger';

/**
 * Header component for the application
 * @param {Object} props - Component props
 * @returns {React.Element} Rendered Header component
 */
const Header = ({ title = 'React App' }) => {
  logger.debug('Rendering Header component', { title });
  
  return (
    <header className="app-header">
      <div className="container">
        <h1>{title}</h1>
        <nav>
          <ul>
            <li>
              <Link to="/">Home</Link>
            </li>
            <li>
              <Link to="/about">About</Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
};

Header.propTypes = {
  title: PropTypes.string
};

export default Header;
