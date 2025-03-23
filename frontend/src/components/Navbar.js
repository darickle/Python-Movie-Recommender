import React from 'react';
import { Link } from 'react-router-dom';
import { isAuthenticated, logoutUser } from '../services/authService';
import '../styles/Navbar.css'; // Updated import path

const Navbar = () => {
  const handleLogout = () => {
    logoutUser();
    window.location.href = '/login'; // Redirect to login page after logout
  };

  return (
    <nav className="navbar">
      <div className="navbar-logo">
        <Link to="/" className="navbar-link">
          MovieApp
        </Link>
      </div>
      <div className="navbar-links">
        <Link to="/" className="navbar-link">
          Home
        </Link>
        {isAuthenticated() ? (
          <>
            <Link to="/watchlist" className="navbar-link">
              Watchlist
            </Link>
            <button onClick={handleLogout} className="navbar-button">
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="navbar-link">
              Login
            </Link>
            <Link to="/register" className="navbar-link">
              Register
            </Link>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;