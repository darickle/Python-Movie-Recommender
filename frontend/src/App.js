/* 
 * Darick Le
 * March 22 2025
 * Api service for managing API requests
 * This file contains the main application logic, including routing and authentication.
 * It uses React Router for navigation and axios for API requests.
 * The application includes components for login, registration, streaming setup, home page,
 * movie detail, watchlist, profile, and discover.
 * The application also handles API connection errors and token expiration.
 */

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate, useLocation } from 'react-router-dom';
import axios from 'axios';

// Components
import Navbar from './components/Navbar';
import Login from './components/Login';
import Register from './components/Register';
import StreamingSetup from './components/StreamingSetup';
import Home from './components/Home';
import MovieDetail from './components/MovieDetail';
import Watchlist from './components/Watchlist';
import Profile from './components/Profile';
import Discover from './components/Discover';  // Import the new Discover component

// API configuration
const API_URL = 'http://localhost:5000/api';

// Configure axios defaults
axios.defaults.baseURL = API_URL;

// Add response interceptor for better error handling
axios.interceptors.response.use(
  response => response,
  error => {
    // Handle API connection errors
    if (error.code === 'ERR_NETWORK') {
      console.error('Network error - Cannot connect to the backend server');
      // You can add UI notification here
    }
    
    // Handle token expiration
    if (error.response && error.response.status === 401) {
      if (error.response.data.code === 'token_expired') {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

axios.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [apiConnected, setApiConnected] = useState(false);
  const [isInitialSetup, setIsInitialSetup] = useState(false);

  useEffect(() => {
    // Check backend connection - update to use ApiService
    import('./components/ApiService').then(module => {
      const ApiService = module.default;
      ApiService.testConnection()
        .then(response => {
          console.log('API connection successful:', response.data);
          setApiConnected(true);
        })
        .catch(error => {
          console.error('Backend connection error:', error);
          setApiConnected(false);
        })
        .finally(() => {
          const token = localStorage.getItem('token');
          const userInfo = localStorage.getItem('user');
          
          if (token && userInfo) {
            try {
              if (typeof userInfo === 'string' && userInfo.trim()) {
                const userData = JSON.parse(userInfo);
                if (userData) {
                  setIsAuthenticated(true);
                  setUser(userData);
                  
                  // Then fetch the latest user data including preferences
                  ApiService.getCurrentUser()
                    .then(response => {
                      if (response && response.data && response.data.user) {
                        const freshUserData = response.data.user;
                        setUser(freshUserData);
                        localStorage.setItem('user', JSON.stringify(freshUserData));
                      }
                    })
                    .catch(error => {
                      console.error('Error fetching user data:', error);
                      if (error.response?.status === 401) {
                        logout();
                      }
                    });
                }
              } else {
                logout();
              }
            } catch (error) {
              console.error('Error parsing user data:', error);
              logout();
            }
          }
          setLoading(false);
        });
    });
  }, []);

  const login = (token, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setIsAuthenticated(true);
    setUser(userData);
  };

  const handleRegistration = (token, userData) => {
    login(token, userData);
    setIsInitialSetup(true);  // Mark as initial setup
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
    setUser(null);
  };

  const AppContent = () => {
    const location = useLocation();
    return (
      <div className="app">
        {!apiConnected && 
          <div style={{ background: '#ffcccc', padding: '10px', textAlign: 'center' }}>
            Warning: Cannot connect to the backend server. Please check if the server is running.
          </div>
        }
        {/* Only show navbar when not in initial setup */}
        {!(isInitialSetup && location.pathname === '/setup') && 
          <Navbar isAuthenticated={isAuthenticated} logout={logout} user={user} />
        }
        <div className="container">
          <Routes>
            <Route path="/" element={
              isAuthenticated 
                ? <Home user={user} /> 
                : <Navigate to="/login" />
            } />
            <Route path="/login" element={!isAuthenticated ? <Login login={login} /> : <Navigate to="/" />} />
            <Route path="/register" element={!isAuthenticated ? <Register login={handleRegistration} /> : <Navigate to="/setup" />} />
            <Route path="/setup" element={
              isAuthenticated 
                ? <StreamingSetup 
                    user={user} 
                    setUser={setUser} 
                    isInitialSetup={isInitialSetup}
                    clearInitialSetup={() => setIsInitialSetup(false)}
                  /> 
                : <Navigate to="/login" />
            } />
            <Route path="/movie/:id" element={isAuthenticated ? <MovieDetail /> : <Navigate to="/login" />} />
            <Route path="/watchlist" element={isAuthenticated ? <Watchlist /> : <Navigate to="/login" />} />
            <Route path="/profile" element={isAuthenticated ? <Profile user={user} setUser={setUser} /> : <Navigate to="/login" />} />
            <Route path="/discover" element={isAuthenticated ? <Discover /> : <Navigate to="/login" />} />
          </Routes>
        </div>
      </div>
    );
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;