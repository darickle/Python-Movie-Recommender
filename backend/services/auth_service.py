from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from datetime import timedelta

def register_user(db, username, password):
    """Register a new user."""
    # Check if the username already exists
    if db.users.find_one({'username': username}):
        return jsonify({'message': 'Username already exists'}), 400

    # Hash the password and save the user
    hashed_password = generate_password_hash(password)
    db.users.insert_one({'username': username, 'password': hashed_password})
    return jsonify({'message': 'User registered successfully'}), 201

def login_user(db, username, password):
    """Authenticate a user and return a JWT token."""
    # Find the user in the database
    user = db.users.find_one({'username': username})
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid username or password'}), 401

    # Create a JWT token
    access_token = create_access_token(identity=str(user['_id']), expires_delta=timedelta(days=1))
    return jsonify({'access_token': access_token}), 200