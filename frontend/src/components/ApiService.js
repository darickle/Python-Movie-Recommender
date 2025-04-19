import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

// Configure axios for this service with improved timeout handling
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10000, // 10 seconds timeout
  headers: {
    'Content-Type': 'application/json'
  },
  // Add retry logic
  retryConfig: {
    retries: 2,
    retryDelay: (retryCount) => {
      return retryCount * 1000; // 1s, 2s, 3s
    }
  }
});

// Add auth token to requests
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

// Add request timeout and retry logic
apiClient.interceptors.response.use(
  response => response,
  async error => {
    const { config, response } = error;
    const retryConfig = config.retryConfig || {};
    
    // Handle token expiration
    if (response?.status === 401 && response?.data?.code === 'token_expired') {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
      return Promise.reject(error);
    }

    // Check if we should retry the request
    if (config && retryConfig && !config._retryCount) {
      config._retryCount = 1;
    } else if (config && config._retryCount) {
      config._retryCount++;
    }
    
    // Determine if we should retry
    if (config && retryConfig && config._retryCount <= retryConfig.retries) {
      // Timeout or network error or 500 errors
      if (!response || response.status >= 500) {
        console.log(`Retrying request (${config._retryCount}/${retryConfig.retries})...`);
        
        // Wait before retrying
        const delay = retryConfig.retryDelay ? 
          retryConfig.retryDelay(config._retryCount) : 
          1000 * config._retryCount;
        
        await new Promise(resolve => setTimeout(resolve, delay));
        return apiClient(config);
      }
    }
    
    return Promise.reject(error);
  }
);

// Enhanced error handling wrapper
const handleApiRequest = async (apiCall) => {
  try {
    const response = await apiCall();
    if (response.status === 200) {
      return {
        data: response.data,
        error: null
      };
    } else {
      console.error('API error:', response.status, response.data);
      return {
        data: null,
        error: response.data?.error || 'Unknown error occurred'
      };
    }
  } catch (error) {
    console.error('API request failed:', error);
    
    // Handle different error types
    if (error.code === 'ECONNABORTED') {
      return {
        data: null,
        error: 'Request timed out. Please try again.'
      };
    }
    
    if (error.response) {
      return {
        data: null,
        error: error.response.data?.error || 'Server error occurred'
      };
    }
    
    return {
      data: null,
      error: error.message || 'Network error occurred'
    };
  }
};

// API service methods
const ApiService = {
  // Test connection
  testConnection: () => {
    return handleApiRequest(() => apiClient.get('/status'));
  },
  
  // Authentication
  login: (credentials) => {
    return apiClient.post('/login', credentials);
  },
  
  register: (userData) => {
    return apiClient.post('/register', userData);
  },
  
  // Streaming services
  getStreamingServices: () => {
    return handleApiRequest(() => apiClient.get('/streaming_services'));
  },
  
  updateUserStreamingServices: (services) => {
    return handleApiRequest(() => apiClient.put('/user/streaming_services', { streaming_services: services }));
  },
  
  getUserStreamingServices: () => {
    return handleApiRequest(() => apiClient.get('/user/streaming_services'));
  },
  
  // Content - now using RapidAPI
  searchContent: (query) => {
    return handleApiRequest(() => apiClient.get('/search', {
      params: { query: encodeURIComponent(query) }
    }));
  },
  
  getContentDetails: (contentId) => {
    return handleApiRequest(() => apiClient.get(`/content/${contentId}`));
  },
  
  // Recommendations
  getRecommendations: () => {
    return handleApiRequest(() => apiClient.get('/recommendations'));
  },
  
  // Watchlist
  getWatchlist: () => {
    return handleApiRequest(() => apiClient.get('/watchlist'));
  },
  
  addToWatchlist: (contentId) => {
    return handleApiRequest(() => apiClient.post('/watchlist', { content_id: contentId }));
  },
  
  // Ratings
  addRating: (contentId, rating, review = '') => {
    return handleApiRequest(() => apiClient.post('/ratings', { 
      content_id: contentId, 
      rating, 
      review 
    }));
  },
  
  getRating: (contentId) => {
    return handleApiRequest(() => apiClient.get(`/ratings/${contentId}`));
  },
  
  // Trending
  getTrending: () => {
    return handleApiRequest(() => apiClient.get('/trending'));
  },
  
  // Discover content from RapidAPI
  getDiscoverCategories: () => {
    return handleApiRequest(() => apiClient.get('/discover/categories'));
  },
  
  getContentByCategory: (category) => {
    return handleApiRequest(() => apiClient.get(`/discover/category/${category}`));
  },
  
  // Get next content for discovery with specific shorter timeout
  getNextContent: (options = {}) => {
    const config = {
      timeout: 8000, // 8 seconds timeout for this specific request
      retryConfig: {
        retries: 1,
        retryDelay: () => 1000
      }
    };
    
    if (options.streamingServices) {
      config.params = { services: options.streamingServices.join(',') };
    }
    
    return handleApiRequest(() => apiClient.get('/discover/next', config));
  },
  
  // Record user preference (like/dislike)
  recordPreference: (contentId, preference) => {
    return handleApiRequest(() => apiClient.post('/discover/preference', {
      content_id: contentId,
      preference: preference
    }));
  },

  // User preferences
  updateUserPreferences: (preferences) => {
    return handleApiRequest(() => apiClient.put('/user/preferences', { preferences }));
  },
  
  // Get current user data
  getCurrentUser: () => {
    return handleApiRequest(() => apiClient.get('/user'));
  }
};

export default ApiService;
