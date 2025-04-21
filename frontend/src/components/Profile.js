/* 
 * Darick Le
 * March 22 2025
 * Api service for managing API requests
 * Shows the user's profile information
 * Allows the user to update their profile information
 * Allows the user to select their preferred genres
 * Allows the user to manage their streaming services
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import ApiService from './ApiService';
import '../styles/profile.css'; // Import the profile styles
import '../styles/forms.css'; // Import form styles for form elements
import '../styles/buttons.css'; // Import button styles

function Profile({ user, setUser }) {
  const [email, setEmail] = useState('');
  const [genres, setGenres] = useState([]);
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  useEffect(() => {
    // Set initial email from user prop
    if (user) {
      setEmail(user.email);
      
      // If user has preference data
      if (user.preferences && user.preferences.genres) {
        setSelectedGenres(user.preferences.genres);
      }
    }
    
    // Fetch available genres
    const fetchGenres = async () => {
      try {
        // In a real app, you'd fetch genres from your API
        // For this example, we'll use a hardcoded list
        setGenres([
          'Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 
          'Documentary', 'Drama', 'Family', 'Fantasy', 'History',
          'Horror', 'Music', 'Mystery', 'Romance', 'Science Fiction',
          'Thriller', 'War', 'Western'
        ]);
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching genres:', error);
        setLoading(false);
      }
    };

    fetchGenres();
  }, [user]);

  const handleGenreToggle = (genre) => {
    if (selectedGenres.includes(genre)) {
      setSelectedGenres(selectedGenres.filter(g => g !== genre));
    } else {
      setSelectedGenres([...selectedGenres, genre]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    
    try {
      await ApiService.updateUserPreferences({
        genres: selectedGenres
      });
      
      // Update local user state
      const updatedUser = { 
        ...user, 
        preferences: { 
          ...user.preferences,
          genres: selectedGenres 
        }
      };
      
      setUser(updatedUser);
      localStorage.setItem('user', JSON.stringify(updatedUser));
      
      setMessage('Profile updated successfully!');
      
      // Clear the message after 3 seconds
      setTimeout(() => {
        setMessage('');
      }, 3000);
    } catch (error) {
      console.error('Error updating preferences:', error);
      setMessage('Failed to update profile. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading profile...</p>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="profile">
        <h2>Your Profile</h2>
        
        {message && (
          <div className={`message-banner ${message.includes('Failed') ? 'error-message' : 'success-message'}`}>
            {message}
          </div>
        )}
        
        <div className="profile-section">
          <h3>Account Information</h3>
          <p><strong>Email:</strong> {email}</p>
        </div>
        
        <form onSubmit={handleSubmit} className="profile-form">
          <div className="profile-section">
            <h3>Genre Preferences</h3>
            <p>Select genres you're interested in:</p>
            
            <div className="genres-grid">
              {genres.map(genre => (
                <div key={genre} className="genre-item">
                  <input
                    type="checkbox"
                    id={`genre-${genre}`}
                    checked={selectedGenres.includes(genre)}
                    onChange={() => handleGenreToggle(genre)}
                  />
                  <label htmlFor={`genre-${genre}`}>{genre}</label>
                </div>
              ))}
            </div>
          </div>
          
          <button type="submit" className="btn btn-primary">Save Preferences</button>
        </form>
        
        <div className="profile-section">
          <h3>Streaming Services</h3>
          <p>Manage which streaming services you use:</p>
          <Link to="/setup" className="btn btn-outline">Edit Streaming Services</Link>
        </div>
      </div>
    </div>
  );
}

export default Profile;