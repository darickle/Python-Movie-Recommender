import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import ApiService from './ApiService';
import '../styles/home.css';

function Home({ user }) {
  const [recommendations, setRecommendations] = useState([]);
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Check if user has streaming services setup
        if (!user.streaming_services || user.streaming_services.length === 0) {
          setError('Please set up your streaming services first');
          setLoading(false);
          return;
        }

        // Fetch recommendations and trending content in parallel
        const [recommendationsResponse, trendingResponse] = await Promise.all([
          ApiService.getRecommendations(),
          ApiService.getTrending()
        ]);

        setRecommendations(recommendationsResponse.data);
        setTrending(trendingResponse.data);
      } catch (err) {
        console.error('Error fetching home data:', err);
        setError('Failed to load content. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user]);

  // Function to add movie to watchlist
  const addToWatchlist = async (contentId) => {
    try {
      await ApiService.addToWatchlist(contentId);
      alert('Added to your watchlist!');
    } catch (error) {
      console.error('Error adding to watchlist:', error);
    }
  };

  if (loading) return <div>Loading...</div>;
  
  if (error) {
    return (
      <div className="setup-prompt">
        <p>{error}</p>
        {(!user.streaming_services || user.streaming_services.length === 0) && (
          <Link to="/setup" className="btn btn-primary">
            Set Up Streaming Services
          </Link>
        )}
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