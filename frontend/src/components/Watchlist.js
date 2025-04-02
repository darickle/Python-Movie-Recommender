import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

function Watchlist() {
const [watchlist, setWatchlist] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  const fetchWatchlist = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/watchlist');
      setWatchlist(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching watchlist:', error);
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
  }
};

if (loading) {
  return <div>Loading your watchlist...</div>;
}

if (watchlist.length === 0) {
  return (
    <div className="watchlist-empty">
      <h2>Your Watchlist</h2>
      <p>You haven't added any movies or shows to your watchlist yet.</p>
      <Link to="/" className="btn">Discover Content</Link>
    </div>
  );
}

return (
  <div className="watchlist">
    <h2>Your Watchlist</h2>
    <div className="watchlist-grid">
      {watchlist.map(item => (
        <div key={item.watchlist_id} className="watchlist-item">
          <img 
            src={item.content.poster_url || 'https://via.placeholder.com/150x225?text=No+Image'} 
            alt={item.content.title}
          />
          <div className="watchlist-item-info">
            <h3>{item.content.title}</h3>
            <p>{item.content.year} • {item.content.runtime_minutes} min</p>
            <p className="added-date">Added on {new Date(item.added_date).toLocaleDateString()}</p>
            
            <div className="watchlist-actions">
              <Link to={`/movie/${item.content.id}`} className="btn btn-small">
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
  </div>
);
}

export default Watchlist;