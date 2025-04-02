import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

function MovieDetail() {
  const { id } = useParams();
  const [content, setContent] = useState(null);
  const [userRating, setUserRating] = useState(0);
  const [review, setReview] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchContentDetails = async () => {
      try {
        const response = await axios.get(`http://localhost:5000/api/content/${id}`);
        setContent(response.data);
        
        // Check if user has already rated this content
        try {
          const ratingResponse = await axios.get(`http://localhost:5000/api/ratings/${id}`);
          if (ratingResponse.data) {
            setUserRating(ratingResponse.data.rating);
            setReview(ratingResponse.data.review || '');
          }
        } catch (error) {
          // User hasn't rated this content yet, which is fine
        }
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching content details:', error);
        setLoading(false);
      }
    };

    fetchContentDetails();
  }, [id]);

  const handleRatingSubmit = async (e) => {
    e.preventDefault();
    
    try {
      await axios.post('http://localhost:5000/api/ratings', {
        content_id: id,
        rating: userRating,
        review: review
      });
      
      alert('Your rating has been submitted!');
    } catch (error) {
      console.error('Error submitting rating:', error);
    }
  };

  const addToWatchlist = async () => {
    try {
      await axios.post('http://localhost:5000/api/watchlist', {
        content_id: id
      });
      
      alert('Added to your watchlist!');
    } catch (error) {
      console.error('Error adding to watchlist:', error);
    }
  };

  if (loading) {
    return <div>Loading content details...</div>;
  }

  if (!content) {
    return <div>Content not found</div>;
  }

  return (
    <div className="movie-detail">
      <div className="content-header">
        <img 
          src={content.poster_url || 'https://via.placeholder.com/300x450?text=No+Image'} 
          alt={content.title}
          className="content-poster"
        />
        
        <div className="content-info">
          <h1>{content.title} ({content.year})</h1>
          <div className="content-meta">
            <span>{content.runtime_minutes} min</span>
            <span>{content.genre_names?.join(', ')}</span>
            <span>Rating: {content.user_rating}/10</span>
          </div>
          
          <p className="content-plot">{content.plot_overview}</p>
          
          <div className="content-credits">
            <p><strong>Director:</strong> {content.directors?.join(', ')}</p>
            <p><strong>Cast:</strong> {content.cast?.slice(0, 5).join(', ')}</p>
          </div>
          
          <div className="content-actions">
            <button onClick={addToWatchlist} className="btn">
              Add to Watchlist
            </button>
          </div>
          
          <div className="streaming-availability">
            <h3>Where to Watch</h3>
            {content.sources?.length > 0 ? (

                // components/MovieDetail.js (continued from previous part)
              <ul className="services-list">
              {content.sources?.map(source => (
                <li key={source.source_id}>
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
          ></textarea>
        </div>
        
        <button type="submit" className="btn">Submit Rating</button>
      </form>
    </div>
    
    <div className="similar-content">
      <h3>Similar Titles</h3>
      <div className="content-row">
        {content.similar_titles?.slice(0, 5).map(similar => (
          <div key={similar.id} className="content-card-small">
            <img 
              src={similar.poster_url || 'https://via.placeholder.com/100x150?text=No+Image'} 
              alt={similar.title}
            />
            <h4>{similar.title}</h4>
            <a href={`/movie/${similar.id}`}>View</a>
          </div>
        ))}
      </div>
    </div>
  </div>
);
}

export default MovieDetail;