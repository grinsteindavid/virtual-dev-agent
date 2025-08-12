/**
 * Logger utility for consistent logging throughout the application
 * This follows the guidelines from gemini-guidelines.md
 */

const LOG_LEVELS = {
  ERROR: 'error',
  WARN: 'warn',
  INFO: 'info',
  DEBUG: 'debug'
};

/**
 * Format log data with consistent structure
 * @param {string} level - Log level
 * @param {string} message - Log message
 * @param {Object} [data] - Additional data to log
 * @returns {Object} Formatted log object
 */
const formatLog = (level, message, data = {}) => {
  return {
    timestamp: new Date().toISOString(),
    level,
    message,
    ...data
  };
};

/**
 * Log to console with appropriate styling
 * @param {string} level - Log level
 * @param {string} message - Log message
 * @param {Object} [data] - Additional data to log
 */
const logToConsole = (level, message, data = {}) => {
  const logObject = formatLog(level, message, data);
  
  switch (level) {
    case LOG_LEVELS.ERROR:
      console.error(logObject);
      break;
    case LOG_LEVELS.WARN:
      console.warn(logObject);
      break;
    case LOG_LEVELS.INFO:
      console.info(logObject);
      break;
    case LOG_LEVELS.DEBUG:
      console.debug(logObject);
      break;
    default:
      console.log(logObject);
  }
};

const logger = {
  /**
   * Log error message
   * @param {string} message - Error message
   * @param {Object} [data] - Additional error data
   */
  error: (message, data = {}) => {
    logToConsole(LOG_LEVELS.ERROR, message, data);
  },
  
  /**
   * Log warning message
   * @param {string} message - Warning message
   * @param {Object} [data] - Additional warning data
   */
  warn: (message, data = {}) => {
    logToConsole(LOG_LEVELS.WARN, message, data);
  },
  
  /**
   * Log info message
   * @param {string} message - Info message
   * @param {Object} [data] - Additional info data
   */
  info: (message, data = {}) => {
    logToConsole(LOG_LEVELS.INFO, message, data);
  },
  
  /**
   * Log debug message
   * @param {string} message - Debug message
   * @param {Object} [data] - Additional debug data
   */
  debug: (message, data = {}) => {
    logToConsole(LOG_LEVELS.DEBUG, message, data);
  }
};

export default logger;
