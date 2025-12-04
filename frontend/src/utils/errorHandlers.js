/**
 * Centralized error handling utilities for frontend
 */

/**
 * Extract user-friendly error message from API error response
 *
 * @param {Error} error - The error object from axios or fetch
 * @param {string} defaultMessage - Default message if no specific error found
 * @returns {Object} - { message, errorCode, details }
 */
export function extractErrorMessage(
  error,
  defaultMessage = "An error occurred"
) {
  // Check if it's an axios error with response
  if (error.response) {
    const { data, status } = error.response;

    // Handle structured error responses
    if (data && typeof data === "object") {
      // New structured error format
      if (data.error_code && data.message) {
        return {
          message: data.message,
          errorCode: data.error_code,
          details: data.details || {},
          status,
        };
      }

      // FastAPI detail format
      if (data.detail) {
        // Detail can be string or object
        if (typeof data.detail === "string") {
          return {
            message: data.detail,
            errorCode: getErrorCodeFromStatus(status),
            details: {},
            status,
          };
        } else if (typeof data.detail === "object") {
          return {
            message: data.detail.message || data.detail.error || defaultMessage,
            errorCode: data.detail.error_code || getErrorCodeFromStatus(status),
            details: data.detail.details || {},
            status,
          };
        }
      }

      // Generic message field
      if (data.message) {
        return {
          message: data.message,
          errorCode: data.error_code || getErrorCodeFromStatus(status),
          details: data.details || {},
          status,
        };
      }
    }

    // Fallback to status-based messages
    return {
      message: getStatusMessage(status, defaultMessage),
      errorCode: getErrorCodeFromStatus(status),
      details: {},
      status,
    };
  }

  // Network error or request setup error
  if (error.request) {
    return {
      message: "Network error. Please check your connection and try again.",
      errorCode: "NETWORK_ERROR",
      details: {},
      status: 0,
    };
  }

  // Generic error
  return {
    message: error.message || defaultMessage,
    errorCode: "UNKNOWN_ERROR",
    details: {},
    status: 0,
  };
}

/**
 * Get error code from HTTP status
 */
function getErrorCodeFromStatus(status) {
  const statusMap = {
    400: "VALIDATION_ERROR",
    401: "AUTHENTICATION_ERROR",
    403: "AUTHORIZATION_ERROR",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT_EXCEEDED",
    500: "INTERNAL_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
    504: "GATEWAY_TIMEOUT",
  };

  return statusMap[status] || "UNKNOWN_ERROR";
}

/**
 * Get user-friendly message from HTTP status
 */
function getStatusMessage(status, defaultMessage) {
  const statusMessages = {
    400: "Invalid request. Please check your input.",
    401: "Authentication required. Please log in again.",
    403: "Access denied. You don't have permission to perform this action.",
    404: "Resource not found.",
    409: "Conflict. The resource already exists or is in use.",
    422: "Validation error. Please check your input.",
    429: "Too many requests. Please try again later.",
    500: "Server error. Please try again later.",
    502: "Service temporarily unavailable. Please try again.",
    503: "Service unavailable. Please try again later.",
    504: "Request timeout. Please try again.",
  };

  return statusMessages[status] || defaultMessage;
}

/**
 * Get user-friendly message for connection errors
 */
export function getConnectionErrorMessage(errorCode, details = {}) {
  const messages = {
    INVALID_CREDENTIALS: {
      title: "Authentication Failed",
      message:
        "The username or password is incorrect. Please verify your credentials.",
      icon: "🔐",
    },
    CONNECTION_TIMEOUT: {
      title: "Connection Timeout",
      message: `Could not connect to ${
        details.host || "the database"
      }. The server may be unreachable or not responding.`,
      icon: "⏱️",
    },
    CONNECTION_REFUSED: {
      title: "Connection Refused",
      message: `The database server at ${
        details.host || "the specified address"
      } refused the connection. It may not be running or configured to accept connections.`,
      icon: "🚫",
    },
    DATABASE_NOT_FOUND: {
      title: "Database Not Found",
      message: `The database '${
        details.database || "specified"
      }' does not exist on the server.`,
      icon: "❓",
    },
    HOST_NOT_FOUND: {
      title: "Host Not Found",
      message: `Could not find the host '${
        details.host || "specified"
      }'. Please check the hostname.`,
      icon: "🌐",
    },
    SSL_ERROR: {
      title: "SSL/TLS Error",
      message:
        "SSL/TLS connection error. The database may require SSL or have certificate issues.",
      icon: "🔒",
    },
    CONFIGURATION_ERROR: {
      title: "Configuration Error",
      message:
        "Server configuration error. Please contact the system administrator.",
      icon: "⚙️",
    },
  };

  return (
    messages[errorCode] || {
      title: "Connection Error",
      message: "Failed to connect to the database. Please check your settings.",
      icon: "⚠️",
    }
  );
}

/**
 * Get user-friendly message for sync errors
 */
export function getSyncErrorMessage(errorCode, details = {}) {
  const messages = {
    PERMISSION_DENIED: {
      title: "Permission Denied",
      message:
        "The database user lacks necessary permissions. Please ensure the user has SELECT permissions on the specified table.",
      icon: "🔐",
    },
    TABLE_NOT_FOUND: {
      title: "Table Not Found",
      message: `The table '${
        details.table || "specified"
      }' does not exist. The database schema may have changed.`,
      icon: "📋",
    },
    COLUMN_NOT_FOUND: {
      title: "Column Not Found",
      message:
        "One or more columns were not found. Please verify the column names in your configuration.",
      icon: "📊",
    },
    SCHEMA_MISMATCH: {
      title: "Schema Mismatch",
      message:
        "The table structure doesn't match the expected format. Column types may be incorrect.",
      icon: "🔧",
    },
    QUOTA_EXCEEDED: {
      title: "Storage Quota Exceeded",
      message:
        "Storage quota has been exceeded. Please free up space or contact your administrator.",
      icon: "💾",
    },
    CREDENTIALS_UNAVAILABLE: {
      title: "Credentials Unavailable",
      message:
        "Credentials are not available. The source may have been rejected or revoked.",
      icon: "🔑",
    },
  };

  return (
    messages[errorCode] || {
      title: "Sync Error",
      message: "Failed to synchronize data. Please check the error details.",
      icon: "⚠️",
    }
  );
}

/**
 * Format error for display in toast notification
 */
export function formatErrorForToast(
  error,
  defaultMessage = "An error occurred"
) {
  const errorInfo = extractErrorMessage(error, defaultMessage);

  // For connection and sync errors, use specialized messages
  if (errorInfo.errorCode && errorInfo.errorCode.includes("CONNECTION")) {
    const connError = getConnectionErrorMessage(
      errorInfo.errorCode,
      errorInfo.details
    );
    return `${connError.icon} ${connError.title}: ${connError.message}`;
  }

  if (
    errorInfo.errorCode &&
    (errorInfo.errorCode.includes("PERMISSION") ||
      errorInfo.errorCode.includes("TABLE") ||
      errorInfo.errorCode.includes("COLUMN") ||
      errorInfo.errorCode.includes("SCHEMA") ||
      errorInfo.errorCode.includes("QUOTA"))
  ) {
    const syncError = getSyncErrorMessage(
      errorInfo.errorCode,
      errorInfo.details
    );
    return `${syncError.icon} ${syncError.title}: ${syncError.message}`;
  }

  // Generic error
  return errorInfo.message;
}

/**
 * Format error for display in error alert/dialog
 */
export function formatErrorForAlert(
  error,
  defaultMessage = "An error occurred"
) {
  const errorInfo = extractErrorMessage(error, defaultMessage);

  let result = {
    title: "Error",
    message: errorInfo.message,
    details: errorInfo.details,
    errorCode: errorInfo.errorCode,
  };

  // Customize based on error type
  if (errorInfo.errorCode && errorInfo.errorCode.includes("CONNECTION")) {
    const connError = getConnectionErrorMessage(
      errorInfo.errorCode,
      errorInfo.details
    );
    result.title = connError.title;
    result.message = connError.message;
    result.icon = connError.icon;
  } else if (
    errorInfo.errorCode &&
    (errorInfo.errorCode.includes("PERMISSION") ||
      errorInfo.errorCode.includes("TABLE") ||
      errorInfo.errorCode.includes("COLUMN") ||
      errorInfo.errorCode.includes("SCHEMA") ||
      errorInfo.errorCode.includes("QUOTA"))
  ) {
    const syncError = getSyncErrorMessage(
      errorInfo.errorCode,
      errorInfo.details
    );
    result.title = syncError.title;
    result.message = syncError.message;
    result.icon = syncError.icon;
  } else if (errorInfo.status === 403) {
    result.title = "Access Denied";
    result.icon = "🚫";
  } else if (errorInfo.status === 404) {
    result.title = "Not Found";
    result.icon = "❓";
  } else if (errorInfo.status === 401) {
    result.title = "Authentication Required";
    result.icon = "🔐";
  }

  // Add hint if available
  if (errorInfo.details && errorInfo.details.hint) {
    result.hint = errorInfo.details.hint;
  }

  return result;
}
