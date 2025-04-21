# Installation Guide

This guide provides step-by-step instructions to set up the MovieApp project on your local machine.

---

## Prerequisites

Ensure you have the following installed on your system:
- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn
- MongoDB (running locally or accessible remotely)

---

## Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.env` file in the `backend` directory and configure the following environment variables:
   ```
   MONGO_URI=mongodb://localhost:27017/media_recommender
   JWT_SECRET_KEY=your-secret-key
   RAPIDAPI_KEY=your-rapidapi-key
   ```

6. Start the backend server:
   ```bash
   python app.py
   ```

---

## Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install the required dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open the application in your browser at:
   ```
   http://localhost:3000
   ```

---

## Additional Notes

- Ensure MongoDB is running before starting the backend server.
- Replace `your-rapidapi-key` in the `.env` file with your actual RapidAPI key.
- For production deployment, configure environment variables securely and use a production-ready database.

