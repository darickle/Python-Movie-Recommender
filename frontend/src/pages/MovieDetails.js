import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { fetchMovieById } from '../services/api';

const MovieDetails = () => {
  const { id } = useParams();
  const [movie, setMovie] = useState(null);

  useEffect(() => {
    const loadMovie = async () => {
      const data = await fetchMovieById(id);
      setMovie(data);
    };
    loadMovie();
  }, [id]);

  if (!movie) return <p>Loading...</p>;

  return (
    <div>
      <h1>{movie.title}</h1>
      <p>Genres: {movie.genres.join(', ')}</p>
      <p>Release Year: {movie.release_year}</p>
      <p>Description: {movie.description}</p>
    </div>
  );
};

export default MovieDetails;