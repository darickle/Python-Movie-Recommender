import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/streaming.css';

function StreamingSetup({ user, setUser }) {
  const [streamingServices, setStreamingServices] = useState([]);
  const [selectedServices, setSelectedServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch available streaming services
    const fetchStreamingServices = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/streaming_services');
        setStreamingServices(response.data);
        
        // Set user's existing selections if any
        if (user && user.streaming_services) {
          setSelectedServices(user.streaming_services);
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

  const handleServiceToggle = (serviceId) => {
    if (selectedServices.includes(serviceId)) {
      setSelectedServices(selectedServices.filter(id => id !== serviceId));
    } else {
      setSelectedServices([...selectedServices, serviceId]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      await axios.put('http://localhost:5000/api/user/streaming_services', {
        streaming_services: selectedServices
      });
      
      // Update local user state
      const updatedUser = { ...user, streaming_services: selectedServices };
      setUser(updatedUser);
      localStorage.setItem('user', JSON.stringify(updatedUser));
      
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
    <div className="container">
      <div className="streaming-setup">
        <h2>Select Your Streaming Services</h2>
        <p>Choose the streaming services you currently subscribe to:</p>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="services-grid">
            {streamingServices.map(service => (
              <div key={service.id} className="service-item">
                <input
                  type="checkbox"
                  id={`service-${service.id}`}
                  checked={selectedServices.includes(service.id)}
                  onChange={() => handleServiceToggle(service.id)}
                />
                <label htmlFor={`service-${service.id}`}>
                  {service.name}
                </label>
              </div>
            ))}
          </div>
          
          <button type="submit" className="btn btn-primary">
            Save Preferences
          </button>
        </form>
      </div>
    </div>
  );
}

export default StreamingSetup;