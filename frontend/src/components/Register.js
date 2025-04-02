import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

function Register({ login }) {
const [email, setEmail] = useState('');
const [password, setPassword] = useState('');
const [confirmPassword, setConfirmPassword] = useState('');
const [error, setError] = useState('');

const handleSubmit = async (e) => {
  e.preventDefault();
  setError('');
  
  if (password !== confirmPassword) {
    setError('Passwords do not match');
    return;
  }
  
  try {
    const response = await axios.post('http://localhost:5000/api/register', {
      email,
      password
    });
    
    // Log user in after successful registration
    login(response.data.token, { email, streaming_services: [] });
  } catch (error) {
    setError(error.response?.data?.error || 'Registration failed. Please try again.');
  }
};

return (
  <div className="auth-container">
    <h2>Create an Account</h2>
    
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
      
      <div className="form-group">
        <label htmlFor="confirm-password">Confirm Password</label>
        <input
          type="password"
          id="confirm-password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />
      </div>
      
      <button type="submit" className="btn btn-primary">Register</button>
    </form>
    
    <p className="auth-redirect">
      Already have an account? <Link to="/login">Log In</Link>
    </p>
  </div>
);
}

export default Register;