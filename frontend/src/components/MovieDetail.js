/* 
 * Darick Le
 * March 22 2025
 * Api service for managing API requests
 * This file contains the MovieDetail component which fetches and displays 
 * detailed information about a movie or TV show. 
 * It includes features such as user ratings, reviews, and watchlist management.
 * The component uses React hooks for state management and side effects.
 */

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import ApiService from './ApiService';
import '../styles/movie-detail.css'; // Import the movie-detail styles

function MovieDetail() {
  const { id } = useParams();
  const [content, setContent] = useState(null);
  const [userRating, setUserRating] = useState(0);
  const [review, setReview] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchContentDetails = async () => {
      try {
        setLoading(true);
        const response = await ApiService.getContentDetails(id);
        console.log('Content details response:', response);

        if (response.error) {
          setError(response.error);
          return;
        }

        if (response.data) {
          console.log('Setting content:', response.data);
          setContent(response.data);
        } else {
          setError('No content data received');
        }
      } catch (error) {
        console.error('Error fetching content details:', error);
        setError('Failed to load content details. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchContentDetails();
    }
  }, [id]);

  const handleRatingSubmit = async (e) => {
    e.preventDefault();
    
    try {
      await ApiService.addRating(id, userRating, review);
      alert('Your rating has been submitted!');
    } catch (error) {
      console.error('Error submitting rating:', error);
    }
  };

  const addToWatchlist = async () => {
    try {
      await ApiService.addToWatchlist(id);
      alert('Added to your watchlist!');
    } catch (error) {
      console.error('Error adding to watchlist:', error);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading content details...</p>
      </div>
    );
  }

  if (error) {
    return <div className="error-container">{error}</div>;
  }

  if (!content) {
    return <div className="container">Content not found</div>;
  }

  // RapidAPI property mappings
  const posterUrl = content.poster_url || 'https://via.placeholder.com/300x450?text=No+Image';
  const title = content.title || '';
  const year = content.year || '';
  const runtime = content.runtime_minutes || 'N/A';
  const genres = (content.genre_names || []).join(', ') || 'N/A';
  const rating = content.us_rating || 'N/A';
  const plot = content.plot_overview || 'No plot description available';
  const directors = (content.directors || []).join(', ') || 'Not available';
  const cast = (content.cast || []).slice(0, 5).join(', ') || 'Not available';

  return (
    <div className="container">
      <div className="movie-detail">
        <div className="content-header">
          <img 
            src={posterUrl} 
            alt={title}
            className="content-poster"
          />
          
          <div className="content-info">
            <h1>{title} ({year})</h1>
            <div className="content-meta">
              <span>{runtime} min</span>
              <span>{genres}</span>
              <span>Rating: {rating}</span>
            </div>
            
            <p className="content-plot">{plot}</p>
            
            <div className="content-credits">
              <p><strong>Director:</strong> {directors}</p>
              <p><strong>Cast:</strong> {cast}</p>
            </div>
            
            <div className="content-actions">
              <button onClick={addToWatchlist} className="btn btn-primary">
                Add to Watchlist
              </button>
            </div>
            
            <div className="streaming-availability">
              <h3>Where to Watch</h3>
              {content.sources && content.sources.length > 0 ? (
                <ul className="services-list">
                  {content.sources.map((source, index) => (
                    <li key={`${source.source_id}-${index}`}>
                      <a href={source.web_url} target="_blank" rel="noopener noreferrer">
                        {source.name} - {source.type}
                      </a>
                    </li>
                  ))}
                </ul>
              ) : (
                <p>Not currently available on your streaming services.</p>
              )}
            </div>
          </div>
        </div>
        
        <div className="user-rating-section">
          <h3>Rate This Title</h3>
          <form onSubmit={handleRatingSubmit} className="rating-form">
            <div className="star-rating">
              {[1, 2, 3, 4, 5].map(star => (
                <span 
                  key={star}
                  className={star <= userRating ? "star active" : "star"}
                  onClick={() => setUserRating(star)}
                >
                  ★
                </span>
              ))}
            </div>
            
            <div className="form-group">
              <label htmlFor="review">Your Review (Optional)</label>
              <textarea
                id="review"
                value={review}
                onChange={(e) => setReview(e.target.value)}
                rows="4"
                placeholder="Share your thoughts about this title..."
                className="form-input"
              ></textarea>
            </div>
            
            <button type="submit" className="btn btn-primary">Submit Rating</button>
          </form>
        </div>
        
        {/* Remove Similar Titles section since it may not be available in the new API */}
      </div>
    </div>
  );
}

export default MovieDetail;