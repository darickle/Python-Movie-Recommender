import React, { useState, useEffect, useCallback } from 'react';
import ApiService from './ApiService';
import '../styles/Discover.css';

function Discover() {
  const [currentContent, setCurrentContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [animationClass, setAnimationClass] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  // Use useCallback to memoize the fetchNextContent function
  const fetchNextContent = useCallback(async () => {
    let timeoutId;
    
    try {
      setLoading(true);
      setError(null);
      
      // Set up a timeout to abort if API call takes too long
      const timeoutPromise = new Promise((_, reject) => {
        timeoutId = setTimeout(() => {
          reject(new Error('Request timed out'));
        }, 8000); // 8 seconds timeout
      });
      
      // Fetch user's streaming services and next content
      const fetchPromise = async () => {
        try {
          return await ApiService.getNextContent();
        } catch (err) {
          console.error('API call error:', err);
          throw err;
        }
      };
      
      // Race between timeout and actual API call
      const response = await Promise.race([fetchPromise(), timeoutPromise]);
      
      // Clear timeout if API call succeeded
      clearTimeout(timeoutId);
      
      if (response.error) {
        throw new Error(response.error);
      }
      
      setCurrentContent(response.data);
    } catch (err) {
      console.error('Error fetching content:', err);
      
      if (err.message === 'Request timed out') {
        setError('The request is taking too long. Please try again.');
      } else if (err.message && err.message.includes('network')) {
        setError('Network error. Please check your internet connection and try again.');
      } else {
        setError('Failed to load content. Please try again.');
      }
      
      // Clear any existing timeout to prevent memory leaks
      if (timeoutId) clearTimeout(timeoutId);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // If we have an error and retry count is less than 3, retry
    if (error && retryCount < 3) {
      const timer = setTimeout(() => {
        console.log(`Retrying... Attempt ${retryCount + 1}`);
        setRetryCount(prevCount => prevCount + 1);
        fetchNextContent();
      }, 2000 * (retryCount + 1)); // Exponential backoff
      
      return () => clearTimeout(timer);
    } else if (!currentContent && !error) {
      // Initial load
      fetchNextContent();
    }
  }, [fetchNextContent, retryCount, error, currentContent]);

  const handlePreference = async (preference) => {
    if (!currentContent) return;

    // Animate the card
    setAnimationClass(`card-exit card-exit-${preference === 'like' ? 'right' : 'left'}`);

    try {
      await ApiService.recordPreference(currentContent.id, preference);
      
      // Wait for animation to complete before fetching next content
      setTimeout(() => {
        setAnimationClass('');
        fetchNextContent();
      }, 300);
    } catch (err) {
      console.error('Error recording preference:', err);
      setError('Failed to record preference. Please try again.');
    }
  };

  const handleRetry = () => {
    setRetryCount(0); // Reset retry count
    setError(null);   // Clear error
    fetchNextContent(); // Try again
  };

  if (loading && !currentContent) {
    return (
      <div className="discover-container">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Finding something you'll love...</p>
        </div>
      </div>
    );
  }

  if (error && !currentContent) {
    return (
      <div className="discover-container">
        <div className="error-message">
          <h3>Oops! Something went wrong</h3>
          <p>{error}</p>
          <button className="btn btn-primary" onClick={handleRetry}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!currentContent) {
    return (
      <div className="discover-container">
        <div className="empty-state">
          <h2>No content to discover!</h2>
          <p>Check back later for more recommendations or try setting up different streaming services.</p>
          <button className="btn btn-primary" onClick={handleRetry}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="discover-container">
      
      <div className="card-container">
        <div className={`content-card ${animationClass}`}>
          <div className="content-info-header">
            <span className="content-type-badge">
              {currentContent.content_type === 'movie' ? 'Movie' : 'TV Show'}
            </span>
            {currentContent.streaming_service && (
              <span className="streaming-service-badge">
                {currentContent.streaming_service.charAt(0).toUpperCase() + currentContent.streaming_service.slice(1)}
              </span>
            )}
          </div>
          <div className="content-image">
            <img 
              src={currentContent.poster_url || 'https://via.placeholder.com/300x450'}
              alt={currentContent.title}
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = 'https://via.placeholder.com/300x450?text=No+Image';
              }}
            />
          </div>
          <div className="content-info">
            <h2>{currentContent.title}</h2>
            <div className="content-meta">
              <span>{currentContent.year}</span>
              {currentContent.runtime_minutes && <span>{currentContent.runtime_minutes} min</span>}
              {currentContent.us_rating && <span>{currentContent.us_rating}</span>}
            </div>
            <p className="content-description">
              {currentContent.plot_overview || 'No description available.'}
            </p>
          </div>
        </div>
      </div>

      <div className="action-buttons">
        <button 
          className="action-button dislike-button"
          onClick={() => handlePreference('dislike')}
        >
          ✕
        </button>
        <button 
          className="action-button like-button"
          onClick={() => handlePreference('like')}
        >
          ♥
        </button>
      </div>
    </div>
  );
}

export default Discover;
