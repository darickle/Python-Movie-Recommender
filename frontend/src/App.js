import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
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

// API configuration
const API_URL = 'http://localhost:5001/api';
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

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userInfo = localStorage.getItem('user');
    
    if (token && userInfo) {
      setIsAuthenticated(true);
      setUser(JSON.parse(userInfo));
    }
    
    setLoading(false);
  }, []);

  const login = (token, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setIsAuthenticated(true);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
    setUser(null);
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <Router>
      <div className="app">
        <Navbar isAuthenticated={isAuthenticated} logout={logout} user={user} />
        <div className="container">
          <Routes>
            <Route path="/" element={isAuthenticated ? <Home user={user} /> : <Navigate to="/login" />} />
            <Route path="/login" element={!isAuthenticated ? <Login login={login} /> : <Navigate to="/" />} />
            <Route path="/register" element={!isAuthenticated ? <Register login={login} /> : <Navigate to="/" />} />
            <Route path="/setup" element={isAuthenticated ? <StreamingSetup user={user} setUser={setUser} /> : <Navigate to="/login" />} />
            <Route path="/movie/:id" element={isAuthenticated ? <MovieDetail /> : <Navigate to="/login" />} />
            <Route path="/watchlist" element={isAuthenticated ? <Watchlist /> : <Navigate to="/login" />} />
            <Route path="/profile" element={isAuthenticated ? <Profile user={user} setUser={setUser} /> : <Navigate to="/login" />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;