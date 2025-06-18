/**
 * Auth utility functions for JWT token handling and validation
 */

/**
 * Decode JWT token without verification (client-side only)
 * @param {string} token - JWT token
 * @returns {object|null} - Decoded payload or null if invalid
 */
export const decodeToken = (token) => {
  try {
    if (!token) return null;

    const parts = token.split(".");
    if (parts.length !== 3) return null;

    const payload = parts[1];
    const decoded = JSON.parse(
      atob(payload.replace(/-/g, "+").replace(/_/g, "/")),
    );

    return decoded;
  } catch (error) {
    console.error("Error decoding token:", error);
    return null;
  }
};

/**
 * Check if JWT token is valid and not expired
 * @param {string} token - JWT token
 * @returns {boolean} - True if valid, false otherwise
 */
export const isTokenValid = (token) => {
  try {
    const decoded = decodeToken(token);
    if (!decoded) return false;

    // Check expiration
    const currentTime = Date.now() / 1000;
    return decoded.exp > currentTime;
  } catch (error) {
    console.error("Error validating token:", error);
    return false;
  }
};

/**
 * Get user data from JWT token
 * @param {string} token - JWT token
 * @returns {object|null} - User data or null if invalid
 */
export const getUserFromToken = (token) => {
  try {
    const decoded = decodeToken(token);
    if (!decoded || !isTokenValid(token)) return null;

    return {
      id: decoded.sub,
      email: decoded.email,
      first_name: decoded.first_name,
      last_name: decoded.last_name,
      role: decoded.role,
      exp: decoded.exp,
      iat: decoded.iat,
    };
  } catch (error) {
    console.error("Error getting user from token:", error);
    return null;
  }
};

/**
 * Get token expiration time
 * @param {string} token - JWT token
 * @returns {Date|null} - Expiration date or null if invalid
 */
export const getTokenExpiration = (token) => {
  try {
    const decoded = decodeToken(token);
    if (!decoded) return null;

    return new Date(decoded.exp * 1000);
  } catch (error) {
    console.error("Error getting token expiration:", error);
    return null;
  }
};

/**
 * Check if user has required role
 * @param {object} user - User object
 * @param {string|array} requiredRoles - Required role(s)
 * @returns {boolean} - True if user has required role
 */
export const hasRole = (user, requiredRoles) => {
  if (!user || !user.role) return false;

  if (Array.isArray(requiredRoles)) {
    return requiredRoles.includes(user.role);
  }

  return user.role === requiredRoles;
};

/**
 * Check if user has admin role
 * @param {object} user - User object
 * @returns {boolean} - True if user is admin
 */
export const isAdmin = (user) => {
  return hasRole(user, "admin");
};

/**
 * Check if user has teacher role
 * @param {object} user - User object
 * @returns {boolean} - True if user is teacher
 */
export const isTeacher = (user) => {
  return hasRole(user, "teacher");
};

/**
 * Check if user has parent role
 * @param {object} user - User object
 * @returns {boolean} - True if user is parent
 */
export const isParent = (user) => {
  return hasRole(user, "parent");
};

/**
 * Get user display name
 * @param {object} user - User object
 * @returns {string} - Display name
 */
export const getUserDisplayName = (user) => {
  if (!user) return "Unknown User";

  const { first_name, last_name, email } = user;

  if (first_name && last_name) {
    return `${first_name} ${last_name}`;
  }

  if (first_name) {
    return first_name;
  }

  return email || "Unknown User";
};

/**
 * Format user role for display
 * @param {string} role - User role
 * @returns {string} - Formatted role
 */
export const formatRole = (role) => {
  if (!role) return "Unknown";

  return role.charAt(0).toUpperCase() + role.slice(1);
};

/**
 * Clear all authentication data
 */
export const clearAuthData = () => {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
};
