#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Change port from 5000 to 5001 to avoid conflict with Apple services
BASE_URL="http://localhost:5001/api"
TOKEN=""

# Function to display result with clear success/failure indication
check_response() {
    if [ $1 -ge 200 ] && [ $1 -lt 300 ]; then
        echo -e "${GREEN}SUCCESS (Status: $1)${NC}"
        echo "$2" | jq . 2>/dev/null || echo "$2"
    else
        echo -e "${RED}FAILED (Status: $1)${NC}"
        echo "$2" | jq . 2>/dev/null || echo "$2"
    fi
    echo ""
}

# Verify server is running with better diagnostics
echo -e "${BLUE}Testing if the server is running...${NC}"
echo -e "${YELLOW}Trying to connect to: ${BASE_URL}/streaming_services${NC}"

# Show the actual curl command being executed
echo -e "${YELLOW}Running: curl -s -o /dev/null -w \"%{http_code}\" ${BASE_URL}/streaming_services${NC}"

# Use more verbose curl to see connection details
response=$(curl -v --max-time 5 -s -o /dev/null -w "%{http_code}" $BASE_URL/streaming_services 2>&1)
curl_exit_code=$?
status_code=$(echo "$response" | tail -n1)

# Better error handling based on curl exit code
if [ $curl_exit_code -ne 0 ]; then
    echo -e "${RED}Connection error: curl exit code $curl_exit_code${NC}"
    echo -e "${YELLOW}Debug information:${NC}"
    echo "$response"
    echo -e "\n${RED}Server is not running or not responding!${NC}"
    echo -e "${YELLOW}How to start the Flask server:${NC}"
    echo "1. Navigate to the backend directory:"
    echo "   cd \"/Users/darickle/Documents/4992 Python/finalProject-darickle/backend\""
    echo "2. Start the Flask application on port 5001 (avoid macOS port conflicts):"
    echo "   python -c \"import app; app.app.run(debug=True, port=5001)\""
    echo "   or"
    echo "   python3 -c \"import app; app.app.run(debug=True, port=5001)\""
    echo "3. Wait until you see the message 'Running on http://127.0.0.1:5001/'"
    echo "4. Run this test script again in a new terminal window"
    echo -e "\n${YELLOW}NOTE: Port 5000 is used by Apple AirPlay on macOS. Using port 5001 instead.${NC}"
    exit 1
elif [ $status_code -ge 200 ] && [ $status_code -lt 300 ]; then
    echo -e "${GREEN}Server is running!${NC}\n"
else
    echo -e "${RED}Server returned unexpected status code: $status_code${NC}"
    echo -e "${YELLOW}Debug information:${NC}"
    echo "$response"
    echo -e "\n${RED}Server is running but might not be functioning correctly!${NC}"
    echo -e "${YELLOW}Port 5000 is being used by Apple services (AirTunes). Try running your Flask app on port 5001 instead:${NC}"
    echo "   cd \"/Users/darickle/Documents/4992 Python/finalProject-darickle/backend\""
    echo "   python -c \"import app; app.app.run(debug=True, port=5001)\""
    exit 1
fi

# 2. Get streaming services
echo -e "${BLUE}Testing GET /api/streaming_services...${NC}"
response=$(curl -s -w "\n%{http_code}" $BASE_URL/streaming_services)
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')
check_response $status_code "$body"

# 3. Register a test user (will fail if user exists, which is okay)
echo -e "${BLUE}Testing POST /api/register...${NC}"
TEST_EMAIL="test_$(date +%s)@example.com"
TEST_PASSWORD="password123"
echo "Using test email: $TEST_EMAIL"

response=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\"}" \
  $BASE_URL/register)
  
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')
check_response $status_code "$body"

# 4. Login with the test user
echo -e "${BLUE}Testing POST /api/login...${NC}"
response=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\"}" \
  $BASE_URL/login)
  
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')
check_response $status_code "$body"

# Extract token from login response
TOKEN=$(echo "$body" | jq -r '.token' 2>/dev/null)
if [ "$TOKEN" != "null" ] && [ "$TOKEN" != "" ]; then
    echo -e "${GREEN}Successfully obtained token!${NC}"
else
    echo -e "${RED}Failed to obtain token, skipping authenticated requests.${NC}"
    exit 1
fi

# 5. Test authenticated endpoint - get user streaming services
echo -e "${BLUE}Testing GET /api/user/streaming_services (authenticated)...${NC}"
response=$(curl -s -w "\n%{http_code}" -X GET \
  -H "Authorization: Bearer $TOKEN" \
  $BASE_URL/user/streaming_services)
  
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')
check_response $status_code "$body"

# 6. Update user streaming services
echo -e "${BLUE}Testing PUT /api/user/streaming_services (authenticated)...${NC}"
response=$(curl -s -w "\n%{http_code}" -X PUT \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"streaming_services\": [\"203\", \"26\", \"372\"]}" \
  $BASE_URL/user/streaming_services)
  
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')
check_response $status_code "$body"

# 7. Test content search
echo -e "${BLUE}Testing GET /api/search...${NC}"
response=$(curl -s -w "\n%{http_code}" "$BASE_URL/search?query=stranger%20things")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')
check_response $status_code "$body"

# 8. Test authenticated recommendations
echo -e "${BLUE}Testing GET /api/recommendations (authenticated)...${NC}"
response=$(curl -s -w "\n%{http_code}" -X GET \
  -H "Authorization: Bearer $TOKEN" \
  $BASE_URL/recommendations)
  
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')
check_response $status_code "$body"

echo -e "${GREEN}Testing completed!${NC}"
