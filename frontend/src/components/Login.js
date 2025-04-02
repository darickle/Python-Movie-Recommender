import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import '../styles/auth.css';

function Login({ login }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      const response = await axios.post('http://localhost:5000/api/login', {
        email,
        password
      });
      
      login(response.data.token, response.data.user);
    } catch (error) {
      setError(error.response?.data?.error || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="auth-container">
        <div className="auth-header">
          <h2>Welcome Back</h2>
          <p className="auth-subtitle">Log in to access your personalized recommendations</p>
        </div>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              className="form-input"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              className="form-input"
            />
            <div className="password-options">
              <Link to="/forgot-password" className="forgot-password">Forgot password?</Link>
            </div>
          </div>
          
          <button 
            type="submit" 
            className={`btn btn-primary login-btn ${isLoading ? 'btn-loading' : ''}`}
            disabled={isLoading}
          >
            {isLoading ? 'Logging in...' : 'Log In'}
          </button>
        </form>
        
        <div className="auth-separator">
          <span>OR</span>
        </div>
        
        <p className="auth-redirect">
          Don't have an account? <Link to="/register" className="auth-link">Sign Up</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;