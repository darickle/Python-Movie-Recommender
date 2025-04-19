import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import ApiService from './ApiService';
import '../styles/./Discover.css';

function Discover() {
  const [content, setContent] = useState({
    trending: [],
    recommended: [],
    categories: {}
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const fetchContent = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch trending content
      const trendingResponse = await ApiService.getTrending();
      console.log('Trending response:', trendingResponse.data);
      
      // Fetch recommendations
      const recommendationsResponse = await ApiService.getRecommendations();
      console.log('Recommendations response:', recommendationsResponse.data);
      
      // Fetch categories (movies, TV shows, etc.)
      const categoriesResponse = await ApiService.getDiscoverCategories();
      console.log('Categories response:', categoriesResponse.data);
      
      setContent({
        trending: trendingResponse.data || [],
        recommended: recommendationsResponse.data || [],
        categories: categoriesResponse.data || {}
      });
      
    } catch (err) {
      console.error('Error fetching discover content:', err);
      setError('Failed to load content. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContent();
  }, []);
  
  const renderContentCard = (item) => {
    if (!item || !item.id) {
      console.warn('Invalid content item:', item);
      return null;
    }
    
    // WatchMode API property mappings
    const title = item.title || item.name;
    const posterUrl = item.poster_url || item.poster || 'https://via.placeholder.com/150x225?text=No+Image';
    const year = item.year || '';
    
    return (
      <div key={item.id} className="content-card">
        <Link to={`/movie/${item.id}`}>
          <div className="content-image">
            <img src={posterUrl} alt={title} />
          </div>
          <div className="content-info">
            <h4>{title}</h4>
            <p>{year}</p>
          </div>
        </Link>
      </div>
    );
  };
  
  const renderContentRow = (title, items) => {
    if (!items || items.length === 0) {
      console.log(`No items for ${title}`);
      return null;
    }
    
    return (
      <div className="content-row">
        <h3>{title}</h3>
        <div className="content-scrollable">
          {items.map(item => renderContentCard(item))}
        </div>
      </div>
    );
  };
  
  if (loading) return <div className="loading">Loading discover content...</div>;
  
  if (error) return (
    <div className="discover-container">
      <h1>Discover</h1>
      <div className="error-container">
        <p className="error-message">{error}</p>
        <button className="retry-button" onClick={fetchContent}>
          Try Again
        </button>
      </div>
    </div>
  );
  
  // Check if we actually have content
  const hasAnyContent = content.trending.length > 0 || 
                        content.recommended.length > 0 || 
                        Object.values(content.categories).some(arr => arr.length > 0);
  
  if (!hasAnyContent) {
    return (
      <div className="discover-container">
        <h1>Discover</h1>
        <div className="no-content-message">
          <p>No content is available for your streaming services.</p>
          <p>Please add more streaming services to your profile or check back later.</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="discover-container">
      <h1>Discover</h1>
      
      {renderContentRow('Trending Now', content.trending)}
      {renderContentRow('Recommended For You', content.recommended)}
      
      {/* Render category sections */}
      {Object.entries(content.categories).map(([category, items]) => (
        items && items.length > 0 ? renderContentRow(category, items) : null
      ))}
    </div>
  );
}

export default Discover;
