import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import '../styles/home.css';

function Home({ user }) {
  const [recommendations, setRecommendations] = useState([]);
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchContent = async () => {
      try {
        // Check if user has selected streaming services
        if (!user.streaming_services || user.streaming_services.length === 0) {
          setLoading(false);
          return;
        }
        
        // Fetch recommendations and trending content
        const [recommendationsRes, trendingRes] = await Promise.all([
          axios.get('http://localhost:5000/api/recommendations'),
          axios.get('http://localhost:5000/api/trending')
        ]);
        
        setRecommendations(recommendationsRes.data);
        setTrending(trendingRes.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching content:', error);
        setLoading(false);
      }
    };

    fetchContent();
  }, [user]);

  // Function to add movie to watchlist
  const addToWatchlist = async (contentId) => {
    try {
      await axios.post('http://localhost:5000/api/watchlist', {
        content_id: contentId
      });
      alert('Added to your watchlist!');
    } catch (error) {
      console.error('Error adding to watchlist:', error);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading recommendations...</p>
      </div>
    );
  }

  // If user hasn't set up streaming services yet
  if (!user.streaming_services || user.streaming_services.length === 0) {
    return (
      <div className="home-no-services">
        <h2>Welcome to Your Personalized Media Recommender!</h2>
        <p>To get started, please tell us which streaming services you use.</p>
        <Link to="/setup" className="btn btn-primary">
          Set Up Your Streaming Services
        </Link>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="home">
        <section className="recommendations">
          <h2>Recommended For You</h2>
          {recommendations.length === 0 ? (
            <div className="empty-state">
              <p>Rate some movies to get personalized recommendations!</p>
              <Link to="/discover" className="btn btn-primary">Discover Movies</Link>
            </div>
          ) : (
            <div className="content-grid">
              {recommendations.map(item => (
                <div key={item.id} className="content-card">
                  <img 
                    src={item.poster_url || 'https://via.placeholder.com/150x225?text=No+Image'} 
                    alt={item.title}
                  />
                  <div className="content-card-body">
                    <h3>{item.title}</h3>
                    <p>{item.year}</p>
                    <div className="card-actions">
                      <Link to={`/movie/${item.id}`} className="btn btn-small">View Details</Link>
                      <button onClick={() => addToWatchlist(item.id)} className="btn btn-small btn-outline">
                        + Watchlist
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="trending">
          <h2>Trending Now</h2>
          <div className="content-grid">
            {trending.map(item => (
              <div key={item.id} className="content-card">
                <img 
                  src={item.poster_url || 'https://via.placeholder.com/150x225?text=No+Image'} 
                  alt={item.title}
                />
                <div className="content-card-body">
                  <h3>{item.title}</h3>
                  <p>{item.year}</p>
                  <div className="card-actions">
                    <Link to={`/movie/${item.id}`} className="btn btn-small">View Details</Link>
                    <button onClick={() => addToWatchlist(item.id)} className="btn btn-small btn-outline">
                      + Watchlist
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

export default Home;