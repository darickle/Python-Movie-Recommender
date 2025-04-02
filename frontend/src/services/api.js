import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

export const fetchMovies = async () => {
  const response = await axios.get(`${API_BASE_URL}/movies`);
  return response.data;
};

export const fetchMovieById = async (id) => {
  const response = await axios.get(`${API_BASE_URL}/movies/${id}`);
  return response.data;
};