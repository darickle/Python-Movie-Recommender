"""
Darick Le
March 11 2025
Validation functions for user registration, login, and movie ID.
"""

from flask import jsonify

def validate_registration_input(data):
    """Validate input for user registration."""
    if not data:
        return jsonify({'message': 'No input provided'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not isinstance(username, str) or len(username) < 3:
        return jsonify({'message': 'Invalid username. Must be at least 3 characters long'}), 400

    if not password or not isinstance(password, str) or len(password) < 6:
        return jsonify({'message': 'Invalid password. Must be at least 6 characters long'}), 400

    return None  # No errors

def validate_login_input(data):
    """Validate input for user login."""
    if not data:
        return jsonify({'message': 'No input provided'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not isinstance(username, str):
        return jsonify({'message': 'Invalid username'}), 400

    if not password or not isinstance(password, str):
        return jsonify({'message': 'Invalid password'}), 400

    return None  # No errors

def validate_movie_id(movie_id):
    """Validate movie ID."""
    if not movie_id or not isinstance(movie_id, str) or len(movie_id) != 24:
        return jsonify({'message': 'Invalid movie ID'}), 400

    return None  # No errors