import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

function Login({ login }) {
const [email, setEmail] = useState('');
const [password, setPassword] = useState('');
const [error, setError] = useState('');

const handleSubmit = async (e) => {
  e.preventDefault();
  setError('');
  
  try {
    const response = await axios.post('http://localhost:5000/api/login', {
      email,
      password
    });
    
    login(response.data.token, response.data.user);
  } catch (error) {
    setError(error.response?.data?.error || 'Login failed. Please try again.');
  }
};

return (
  <div className="auth-container">
    <h2>Log In</h2>
    
    {error && <div className="error-message">{error}</div>}
    
    <form onSubmit={handleSubmit} className="auth-form">
      <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      
      <button type="submit" className="btn btn-primary">Log In</button>
    </form>
    
    <p className="auth-redirect">
      Don't have an account? <Link to="/register">Register</Link>
    </p>
  </div>
);
}

export default Login;