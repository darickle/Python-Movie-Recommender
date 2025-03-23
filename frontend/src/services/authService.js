import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api'; // Replace with your backend URL

// Register a new user
export const registerUser = async (username, password) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/register`, { username, password });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : { message: 'Network Error' };
  }
};

// Login a user
export const loginUser = async (username, password) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/login`, { username, password });
    const { access_token } = response.data;

    // Save the token to localStorage
    localStorage.setItem('access_token', access_token);

    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : { message: 'Network Error' };
  }
};

// Logout a user
export const logoutUser = () => {
  // Remove the token from localStorage
  localStorage.removeItem('access_token');
};

// Get the current user's token
export const getToken = () => {
  return localStorage.getItem('access_token');
};

// Check if the user is authenticated
export const isAuthenticated = () => {
  return !!getToken();
};