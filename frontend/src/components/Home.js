import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import ApiService from './ApiService';
import '../styles/home.css';

function Home({ user, needsSetup }) {
  const [recommendations, setRecommendations] = useState([]);
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch recommendations and trending content in parallel
        const [recommendationsResponse, trendingResponse] = await Promise.all([
          ApiService.getRecommendations(),
          ApiService.getTrending()
        ]);

        console.log('Home: Recommendations response:', recommendationsResponse.data);
        console.log('Home: Trending response:', trendingResponse.data);

        // Check for error property in response
        if (recommendationsResponse.error) {
          console.error('Error fetching recommendations:', recommendationsResponse.error);
        } else {
          setRecommendations(recommendationsResponse.data || []);
        }

        if (trendingResponse.error) {
          console.error('Error fetching trending:', trendingResponse.error);
        } else {
          setTrending(trendingResponse.data || []);
        }
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
      const response = await ApiService.addToWatchlist(contentId);
      if (response.error) {
        console.error('Error response:', response.error);
        alert('Failed to add to watchlist. Please try again.');
      } else {
        alert('Added to your watchlist!');
      }
    } catch (error) {
      console.error('Error adding to watchlist:', error);
      alert('Failed to add to watchlist. Please try again.');
    }
  };

  if (loading) return <div className="loading-container">Loading...</div>;
  
  if (error) {
    return (
      <div className="error-message">
        <p>{error}</p>
      </div>
    );
  }

  const hasNoContent = recommendations.length === 0 && trending.length === 0;

  // Helper function to render consistent content cards with WatchMode data
  const renderContentCard = (item) => {
    const posterUrl = item.poster_url || item.poster || 'https://via.placeholder.com/150x225?text=No+Image';
    const title = item.title || item.name;
    const year = item.year || '';
    
    return (
      <div key={item.id} className="content-card">
        <img src={posterUrl} alt={title} />
        <div className="content-card-body">
          <h3>{title}</h3>
          <p>{year}</p>
          <div className="card-actions">
            <Link to={`/movie/${item.id}`} className="btn btn-small">View Details</Link>
            <button onClick={() => addToWatchlist(item.id)} className="btn btn-small btn-outline">
              + Watchlist
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="home-container">
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
                {recommendations.map(renderContentCard)}
              </div>
            )}
          </section>

          {trending.length > 0 && (
            <section className="trending">
              <h2>Trending Now</h2>
              <div className="content-grid">
                {trending.map(renderContentCard)}
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

export default Home;