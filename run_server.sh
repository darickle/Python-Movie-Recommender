#!/bin/bash

# Navigate to the backend directory
cd "$(dirname "$0")/backend"

# Start Flask on port 5001 to avoid conflicts with macOS AirPlay (which uses port 5000)
echo "Starting Flask server on port 5001..."
python3 -c "import app; app.app.run(debug=True, port=5001)"
