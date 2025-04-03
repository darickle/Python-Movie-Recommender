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

// API service methods
const ApiService = {
  // Test connection
  testConnection: () => {
    return apiClient.get('/status');
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
    return apiClient.get('/streaming_services');
  },
  
  updateUserStreamingServices: (services) => {
    return apiClient.put('/user/streaming_services', { streaming_services: services });
  },
  
  getUserStreamingServices: () => {
    return apiClient.get('/user/streaming_services');
  },
  
  // Content
  searchContent: (query) => {
    return apiClient.get(`/search?query=${encodeURIComponent(query)}`);
  },
  
  getContentDetails: (contentId) => {
    return apiClient.get(`/content/${contentId}`);
  },
  
  // Recommendations
  getRecommendations: () => {
    return apiClient.get('/recommendations');
  },
  
  // Watchlist
  getWatchlist: () => {
    return apiClient.get('/watchlist');
  },
  
  addToWatchlist: (contentId) => {
    return apiClient.post('/watchlist', { content_id: contentId });
  },
  
  // Ratings
  addRating: (contentId, rating, review = '') => {
    return apiClient.post('/ratings', { 
      content_id: contentId, 
      rating, 
      review 
    });
  },
  
  // Trending
  getTrending: () => {
    return apiClient.get('/trending');
  }
};

export default ApiService;
