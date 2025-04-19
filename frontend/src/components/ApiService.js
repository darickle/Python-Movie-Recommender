import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

// Configure axios for this service
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10000, // 10 seconds timeout
  headers: {
    'Content-Type': 'application/json'
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

// Enhanced error handling wrapper
const handleApiRequest = async (apiCall) => {
  try {
    const response = await apiCall();
    return response;
  } catch (error) {
    console.error('API request failed:', error.message);
    
    // Provide more detailed error information
    if (error.response) {
      console.error('Error response:', {
        status: error.response.status,
        data: error.response.data
      });
    } else if (error.request) {
      console.error('No response received from server');
    }
    
    // Return a standardized error response instead of throwing
    return {
      data: [],
      error: error.message
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
  
  // Content - all using WatchMode API
  searchContent: (query) => {
    return handleApiRequest(() => apiClient.get(`/search?query=${encodeURIComponent(query)}`));
  },
  
  getContentDetails: (contentId) => {
    return handleApiRequest(() => apiClient.get(`/content/${contentId}`));
  },
  
  // Recommendations from WatchMode API
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
  
  // Trending from WatchMode API
  getTrending: () => {
    return handleApiRequest(() => apiClient.get('/trending'));
  },
  
  // Discover content from WatchMode API
  getDiscoverCategories: () => {
    return handleApiRequest(() => apiClient.get('/discover/categories'));
  },
  
  getContentByCategory: (category) => {
    return handleApiRequest(() => apiClient.get(`/discover/category/${category}`));
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
