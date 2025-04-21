/* 
 * Darick Le
 * March 22 2025
 * Api service for managing API requests
 * This component allows users to select their streaming services 
 * during the initial setup or update their preferences later.
 * It fetches the available streaming services from the backend,
 * displays them in a grid, and allows users to select or deselect
 * their preferred services. Upon submission, it updates the user's
 * preferences in the backend and navigates to the home page.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/streaming.css';

function StreamingSetup({ user, setUser, isInitialSetup, clearInitialSetup }) {
  const [streamingServices, setStreamingServices] = useState([]);
  const [selectedServices, setSelectedServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch available streaming services
    const fetchStreamingServices = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get('http://localhost:5000/api/streaming_services', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setStreamingServices(response.data);
        
        // Set user's existing selections if any
        if (user && user.streaming_services) {
          setSelectedServices(user.streaming_services.map(id => id.toString()));
        }
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching streaming services:', error);
        setError('Failed to load streaming services. Please try again later.');
        setLoading(false);
      }
    };

    fetchStreamingServices();
  }, [user]);

  const handleServiceToggle = (sourceId) => {
    setSelectedServices(prev => {
      const sourceIdStr = sourceId.toString();
      if (prev.includes(sourceIdStr)) {
        return prev.filter(id => id !== sourceIdStr);
      } else {
        return [...prev, sourceIdStr];
      }
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        'http://localhost:5000/api/user/streaming_services',
        { streaming_services: selectedServices },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Update local user state
      const updatedUser = { ...user, streaming_services: selectedServices };
      setUser(updatedUser);
      localStorage.setItem('user', JSON.stringify(updatedUser));
      
      // Clear initial setup flag if needed
      if (isInitialSetup) {
        clearInitialSetup();
      }
      
      // Navigate to home page after successful update
      navigate('/');
    } catch (error) {
      console.error('Error updating streaming services:', error);
      setError('Failed to update your streaming preferences. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading streaming services...</p>
      </div>
    );
  }

  return (
    <div className={`container ${isInitialSetup ? 'initial-setup' : ''}`}>
      <div className="streaming-setup">
        {isInitialSetup && (
          <div className="welcome-header">
            <h1>Welcome to Watchr!</h1>
            <p>Let's get you set up with your streaming services</p>
          </div>
        )}
      
        <h2>Select Your Streaming Services</h2>
        <p>Choose the streaming services you currently subscribe to:</p>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="services-grid">
            {streamingServices.map(service => (
              <div key={service.source_id} className="service-item">
                <input
                  type="checkbox"
                  id={`service-${service.source_id}`}
                  checked={selectedServices.includes(service.source_id.toString())}
                  onChange={() => handleServiceToggle(service.source_id)}
                />
                <label htmlFor={`service-${service.source_id}`}>
                  {service.name}
                </label>
              </div>
            ))}
          </div>
          
          <button type="submit" className="btn btn-primary">
            {isInitialSetup ? "Let's Go!" : "Save Preferences"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default StreamingSetup;