/* 
 * Darick Le
 * March 22 2025
 * Api service for managing API requests
 * This file contains the Watchlist component which fetches 
 * and displays the user's watchlist. 
 * It allows users to remove items from the watchlist.
 * The component uses React hooks for state management and
 * side effects, and Axios for making HTTP requests.
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import '../styles/watchlist.css';

function Watchlist() {
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchWatchlist = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/watchlist');
        setWatchlist(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching watchlist:', error);
        setError('Failed to load your watchlist. Please try again later.');
        setLoading(false);
      }
    };

    fetchWatchlist();
  }, []);

  const removeFromWatchlist = async (watchlistId) => {
    try {
      await axios.delete(`http://localhost:5000/api/watchlist/${watchlistId}`);
      // Update local state to remove the deleted item
      setWatchlist(watchlist.filter(item => item.watchlist_id !== watchlistId));
    } catch (error) {
      console.error('Error removing from watchlist:', error);
      setError('Failed to remove item from your watchlist. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading your watchlist...</p>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="watchlist">
        <h2>Your Watchlist</h2>
        
        {error && <div className="error-message">{error}</div>}
        
        {watchlist.length === 0 ? (
          <div className="watchlist-empty">
            <p>You haven't added any movies or shows to your watchlist yet.</p>
            <Link to="/" className="btn btn-primary">Discover Content</Link>
          </div>
        ) : (
          <div className="watchlist-grid">
            {watchlist.map(item => (
              <div key={item.watchlist_id} className="watchlist-item">
                <img 
                  src={item.content.poster_url || '/api/placeholder/150/225'} 
                  alt={item.content.title}
                />
                <div className="watchlist-item-info">
                  <h3>{item.content.title}</h3>
                  <p>{item.content.year} • {item.content.runtime_minutes} min</p>
                  <p className="added-date">Added on {new Date(item.added_date).toLocaleDateString()}</p>
                  
                  <div className="watchlist-actions">
                    <Link to={`/movie/${item.content.id}`} className="btn btn-small btn-outline">
                      View Details
                    </Link>
                    <button 
                      onClick={() => removeFromWatchlist(item.watchlist_id)} 
                      className="btn btn-small btn-danger"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Watchlist;