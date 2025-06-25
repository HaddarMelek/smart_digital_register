import axios from "axios";

// Get API URL based on environment
const getApiUrl = () => {
  // Production API URL from environment
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // Development fallback
  if (process.env.NODE_ENV === 'development') {
    return "http://localhost:5000/api";
  }
  
  // Default production API (update this with your actual backend URL)
  return "https://smart-school-backend.herokuapp.com/api";
};

// Create axios instance with base configuration
const api = axios.create({
  baseURL: getApiUrl(),
  timeout: 15000, // Increased timeout for production
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor for debugging
api.interceptors.request.use((config) => {
  if (process.env.NODE_ENV === 'development') {
    console.log(`🌐 API Request: ${config.method?.toUpperCase()} ${config.url}`);
  }
  return config;
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (process.env.NODE_ENV === 'development') {
      console.error('🚨 API Error:', error.response?.data || error.message);
    }
    return Promise.reject(error);
  }
);

// Helper functions for working with standardized API responses
export const ApiHelpers = {
  // Check if response is successful
  isSuccess: (response) => {
    return response && response.data !== undefined;
  },

  // Extract data from response
  getData: (response) => {
    return response?.data || null;
  },

  // Extract message from response
  getMessage: (response) => {
    return response?.message || "Success";
  },

  // Extract metadata (pagination, etc.)
  getMeta: (response) => {
    return response?.meta || null;
  },

  // Extract pagination info
  getPagination: (response) => {
    return response?.meta?.pagination || null;
  },

  // Handle API errors consistently
  handleError: (error) => {
    return {
      message: error?.message || "An error occurred",
      errors: error?.errors || [],
      errorCode: error?.errorCode || null,
      status: error?.response?.status || null,
    };
  },
};

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("accessToken");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor for standardized API response handling
api.interceptors.response.use(
  (response) => {
    // Extract data from standardized response format
    const responseData = response.data;

    // If it's a standardized response with success field
    if (responseData && typeof responseData.success === "boolean") {
      if (responseData.success) {
        // For successful responses, return the data field
        response.data = responseData.data;
        response.message = responseData.message;
        response.meta = responseData.meta; // For pagination, etc.
        return response;
      } else {
        // For failed responses marked as success: false, treat as error
        const error = new Error(responseData.message || "Request failed");
        error.response = response;
        error.response.data = responseData;
        return Promise.reject(error);
      }
    }

    // For non-standardized responses, return as-is
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response) {
      const { status, data } = error.response;

      // Extract message from standardized error response
      let errorMessage = "An error occurred";
      if (data && data.message) {
        errorMessage = data.message;
      }

      // Log errors with additional context
      const errorDetails = {
        status,
        message: errorMessage,
        errors: data?.errors || [],
        errorCode: data?.error_code || null,
      };

      switch (status) {
        case 400:
          console.error("Bad Request:", errorDetails);
          break;
        case 401:
          console.error("Unauthorized:", errorDetails);
          // Clear tokens on authentication failure
          localStorage.removeItem("accessToken");
          localStorage.removeItem("refreshToken");
          break;
        case 403:
          console.error("Forbidden:", errorDetails);
          break;
        case 404:
          console.error("Not Found:", errorDetails);
          break;
        case 500:
          console.error("Server Error:", errorDetails);
          break;
        default:
          console.error(`HTTP ${status}:`, errorDetails);
      }

      // Enhance error object with standardized data
      error.message = errorMessage;
      error.errors = data?.errors || [];
      error.errorCode = data?.error_code || null;
    } else if (error.request) {
      console.error("Network Error:", "Unable to connect to server");
      error.message = "Unable to connect to server";
    } else {
      console.error("Error:", error.message);
    }

    return Promise.reject(error);
  },
);

export default api;
