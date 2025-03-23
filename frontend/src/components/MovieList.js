import React, { useEffect, useState } from 'react';
import { fetchMovies } from '../services/api';
import MovieCard from './MovieCard';

const MovieList = () => {
  const [movies, setMovies] = useState([]);

  useEffect(() => {
    const loadMovies = async () => {
      const data = await fetchMovies();
      setMovies(data);
    };
    loadMovies();
  }, []);

  return (
    <div className="movie-list">
      {movies.map((movie) => (
        <MovieCard
          key={movie._id}
          title={movie.title}
          genres={movie.genres}
          releaseYear={movie.release_year}
        />
      ))}
    </div>
  );
};

export default MovieList;