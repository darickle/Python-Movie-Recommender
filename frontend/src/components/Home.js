import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import ApiService from './ApiService';
import '../styles/home.css';

function Home({ user }) {
  const [recommendations, setRecommendations] = useState([]);
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch recommendations and trending content in parallel
        const [recommendationsResponse, trendingResponse] = await Promise.all([
          ApiService.getRecommendations(),
          ApiService.getTrending()
        ]);

        console.log('Recommendations response:', recommendationsResponse);
        console.log('Trending response:', trendingResponse);

        // Check for data property
        if (recommendationsResponse.data) {
          setRecommendations(recommendationsResponse.data);
        } else if (recommendationsResponse.error) {
          console.error('Recommendations error:', recommendationsResponse.error);
        }

        if (trendingResponse.data) {
          setTrending(trendingResponse.data);
        } else if (trendingResponse.error) {
          console.error('Trending error:', trendingResponse.error);
        }

      } catch (err) {
        console.error('Error fetching home data:', err);
        
        // Implement retry logic for network errors
        if (retryCount < 3) {
          console.log(`Retrying fetch... Attempt ${retryCount + 1}`);
          setRetryCount(prevCount => prevCount + 1);
          // We'll retry in the next useEffect cycle
        } else {
          setError('Failed to load content. Please check your network connection and try again later.');
        }
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchData();
    }
  }, [user, retryCount]); // Add retryCount to dependencies for retry logic

  // Function to handle manual refresh
  const handleRefresh = () => {
    setRetryCount(0); // Reset retry count to trigger a refresh
    setError(''); // Clear any previous errors
  };

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

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading your personalized content...</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="error-container">
        <h3>Oops! Something went wrong</h3>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={handleRefresh}>
          Try Again
        </button>
      </div>
    );
  }

  // Check if user has no streaming services configured
  const hasNoStreamingServices = !user?.streaming_services || user.streaming_services.length === 0;

  // Helper function to render consistent content cards
  const renderContentCard = (item) => {
    if (!item || !item.id) {
      console.warn('Invalid content item:', item);
      return null;
    }
    
    const title = item.title || 'Unknown Title';
    const posterUrl = item.poster_url || 'https://via.placeholder.com/300x450?text=No+Image';
    const year = item.year || '';

    return (
      <div key={item.id} className="content-card">
        <Link to={`/movie/${item.id}`}>
          <div className="content-image">
            <img 
              src={posterUrl}
              alt={title}
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = 'https://via.placeholder.com/300x450?text=No+Image';
              }}
            />
          </div>
          <div className="content-info">
            <h4>{title}</h4>
            {year && <p>{year}</p>}
          </div>
        </Link>
        <button 
          className="btn btn-small btn-outline watchlist-btn"
          onClick={() => addToWatchlist(item.id)}
          aria-label={`Add ${title} to watchlist`}
        >
          + Watchlist
        </button>
      </div>
    );
  };

  return (
    <div className="home-container">
      <div className="container">
        <div className="home">
          
          {hasNoStreamingServices ? (
            <div className="home-no-services">
              <h2>Welcome to Watchr!</h2>
              <p>Start by setting up your streaming services to get personalized recommendations.</p>
              <Link to="/setup" className="btn btn-primary">Set Up Streaming Services</Link>
            </div>
          ) : (
            <>
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
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default Home;