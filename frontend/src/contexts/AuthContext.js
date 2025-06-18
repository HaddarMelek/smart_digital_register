import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { message } from "antd";
import api from "../services/api";
import { getUserFromToken, isTokenValid } from "../utils/auth";

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check for existing token on app startup
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = () => {
    try {
      const token = localStorage.getItem("accessToken");
      if (token && isTokenValid(token)) {
        const tokenData = getUserFromToken(token);
        if (tokenData) {
          // Extract name and role from token data
          const userData = {
            name: `${tokenData.first_name} ${tokenData.last_name}`.trim(),
            role: tokenData.role,
          };
          setUser(userData);
          setIsAuthenticated(true);
          // Set token in API headers
          api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
        }
      }
    } catch (error) {
      console.error("Error checking auth status:", error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await api.post("/auth/login", {
        email: email.toLowerCase().trim(),
        password,
      });

      const { access_token, refresh_token, user: userInfo } = response.data;

      // Store tokens
      localStorage.setItem("accessToken", access_token);
      localStorage.setItem("refreshToken", refresh_token);

      // Set user data with both name and role from the standardized response
      const userData = {
        name: `${userInfo.first_name} ${userInfo.last_name}`.trim(),
        role: userInfo.role,
        email: userInfo.email,
        id: userInfo.id,
      };
      setUser(userData);
      setIsAuthenticated(true);

      // Set token in API headers
      api.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;

      message.success(`Welcome back, ${userData.name}!`);

      return { success: true, user: userData };
    } catch (error) {
      console.error("Login error:", error);
      const errorMessage = error.message || "Login failed. Please try again.";
      message.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const logout = () => {
    // Clear tokens
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");

    // Clear API headers
    delete api.defaults.headers.common["Authorization"];

    // Clear state
    setUser(null);
    setIsAuthenticated(false);

    message.info("You have been logged out");
  };

  const refreshToken = useCallback(async () => {
    try {
      const refreshToken = localStorage.getItem("refreshToken");
      if (!refreshToken) {
        throw new Error("No refresh token available");
      }

      const response = await api.post(
        "/auth/refresh",
        {},
        {
          headers: {
            Authorization: `Bearer ${refreshToken}`,
          },
        },
      );

      // The api interceptor now extracts the data field automatically
      const { access_token } = response.data;

      // Update stored token
      localStorage.setItem("accessToken", access_token);

      // Update API headers
      api.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;

      return access_token;
    } catch (error) {
      console.error("Token refresh failed:", error);
      logout();
      throw error;
    }
  }, []);

  const updateProfile = async (profileData) => {
    try {
      const response = await api.put("/auth/profile", profileData);
      const updatedUserData = response.data.user;

      // Ensure user object maintains name and role structure
      const userData = {
        name:
          updatedUserData.name ||
          `${updatedUserData.first_name} ${updatedUserData.last_name}`.trim(),
        role: updatedUserData.role,
        email: updatedUserData.email,
        id: updatedUserData.id,
      };

      setUser(userData);
      message.success(response.message || "Profile updated successfully");

      return { success: true, user: userData };
    } catch (error) {
      const errorMessage = error.message || "Failed to update profile";
      message.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const changePassword = async (currentPassword, newPassword) => {
    try {
      const response = await api.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });

      message.success(response.message || "Password changed successfully");
      return { success: true };
    } catch (error) {
      const errorMessage = error.message || "Failed to change password";
      message.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  // Helper function to get user display name
  const getUserDisplayName = (user) => {
    if (!user) return null;
    return user.name || "User";
  };

  // Helper function to get user role
  const getUserRole = (user) => {
    if (!user) return null;
    return user.role || "user";
  };

  // Setup axios interceptor for token refresh
  useEffect(() => {
    const setupInterceptors = () => {
      // Response interceptor for handling token expiration
      api.interceptors.response.use(
        (response) => response,
        async (error) => {
          const originalRequest = error.config;

          if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
              await refreshToken();
              return api(originalRequest);
            } catch (refreshError) {
              logout();
              return Promise.reject(refreshError);
            }
          }

          return Promise.reject(error);
        },
      );
    };

    if (isAuthenticated) {
      setupInterceptors();
    }
  }, [isAuthenticated, refreshToken]);

  const value = {
    isAuthenticated,
    user,
    loading,
    login,
    logout,
    refreshToken,
    updateProfile,
    changePassword,
    checkAuthStatus,
    getUserDisplayName,
    getUserRole,
  };

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          background: "#f0f2f5",
        }}
      >
        <div className="text-center">
          <div className="spinner"></div>
          <p style={{ marginTop: 16, color: "#666" }}>Loading...</p>
        </div>
      </div>
    );
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
