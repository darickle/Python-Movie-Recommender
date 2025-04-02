import React from 'react';
import { Link } from 'react-router-dom';

function Navbar({ isAuthenticated, logout, user }) {
return (
  <nav className="navbar">
    <div className="navbar-brand">
      <Link to="/">MovieMatch</Link>
    </div>
    
    <div className="navbar-menu">
      {isAuthenticated ? (
        <>
          <Link to="/" className="nav-item">Home</Link>
          <Link to="/watchlist" className="nav-item">Watchlist</Link>
          <Link to="/setup" className="nav-item">Services</Link>
          <Link to="/profile" className="nav-item">Profile</Link>
          <button onClick={logout} className="nav-item btn-link">Logout</button>
        </>
      ) : (
        <>
          <Link to="/login" className="nav-item">Login</Link>
          <Link to="/register" className="nav-item">Register</Link>
        </>
      )}
    </div>
  </nav>
);
}

export default Navbar;