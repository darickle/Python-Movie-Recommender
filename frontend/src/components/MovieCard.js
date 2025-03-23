import React from 'react';

const MovieCard = ({ title, genres, releaseYear }) => {
  return (
    <div className="movie-card">
      <h3>{title}</h3>
      <p>Genres: {genres.join(', ')}</p>
      <p>Release Year: {releaseYear}</p>
    </div>
  );
};

export default MovieCard;