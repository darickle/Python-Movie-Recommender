import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../styles/navbar.css';

function Navbar({ isAuthenticated, logout, user }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  
  const toggleMenu = () => {
    setMenuOpen(!menuOpen);
  };
  
  const closeMenu = () => {
    setMenuOpen(false);
  };
  
  const isActive = (path) => {
    return location.pathname === path ? 'active' : '';
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">MovieMatch</Link>
      </div>
      
      <button className="menu-toggle" onClick={toggleMenu}>
        {menuOpen ? '✕' : '☰'}
      </button>
      
      <div className={`navbar-menu ${menuOpen ? 'show' : ''}`}>
        {isAuthenticated ? (
          <>
            <Link to="/" className={`nav-item ${isActive('/')}`} onClick={closeMenu}>Home</Link>
            <Link to="/watchlist" className={`nav-item ${isActive('/watchlist')}`} onClick={closeMenu}>Watchlist</Link>
            <Link to="/setup" className={`nav-item ${isActive('/setup')}`} onClick={closeMenu}>Services</Link>
            <Link to="/profile" className={`nav-item ${isActive('/profile')}`} onClick={closeMenu}>Profile</Link>
            <button onClick={() => { logout(); closeMenu(); }} className="nav-item btn-link">Logout</button>
          </>
        ) : (
          <>
            <Link to="/login" className={`nav-item ${isActive('/login')}`} onClick={closeMenu}>Login</Link>
            <Link to="/register" className={`nav-item ${isActive('/register')}`} onClick={closeMenu}>Register</Link>
          </>
        )}
      </div>
    </nav>
  );
}

export default Navbar;