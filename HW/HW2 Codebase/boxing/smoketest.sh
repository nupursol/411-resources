#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}

##########################################################
#
# Boxer Management
#
##########################################################

create_boxer() {
  name=$1
  weight=$2
  height=$3
  reach=$4
  age=$5

  echo "Creating boxer: $name"
  curl -s -X POST "$BASE_URL/create-boxer" -H "Content-Type: application/json" \
    -d "{\"name\":\"$name\", \"weight\":\"$weight\", \"height\":$height, \"reach\":\"$reach\", \"age\":$age}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Boxer created successfully."
  else
    echo "Failed to create boxer."
    exit 1
  fi
}

delete_boxer_by_id() {
  boxer_id=$1

  echo "Deleting boxer by ID ($boxer_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-boxer/$boxer_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer deleted successfully by ID ($boxer_id)."
  else
    echo "Failed to delete boxer by ID ($boxer_id)."
    exit 1
  fi
}

get_leaderboard() {
  sort=$1

  echo "Getting leaderboard sorted by $sort . . ."
  response=$(curl -s -X GET "$BASE_URL/leaderboard?sort=$sort")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Leaderboard retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Leaderboard JSON (sorted by $sort):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get leaderboard."
    exit 1
  fi
}

get_boxer_by_id() {
  boxer_id=$1

  echo "Getting boxer by ID ($boxer_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-boxer-by-name/$boxer_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer retrieved successfully by ID ($boxer_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Boxer JSON (ID $boxer_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get boxer by ID ($boxer_id)."
    exit 1
  fi
}

get_boxer_by_name() {
  name=$1

  echo "Getting boxer by name ($name)..."
  response=$(curl -s -X GET "$BASE_URL/get-boxer-by-name/$name")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer retrieved successfully by name ($name)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Boxer JSON (name $name):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get boxer by name ($name)."
    exit 1
  fi
}


##########################################################
#
# Fight Management
#
##########################################################

fight() {

  echo "Starting a fight ..."
  response=$(curl -s -X GET "$BASE_URL/fight")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Fight completed successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Fight JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to complete fight."
    exit 1
  fi
}

clear_ring() {

  echo "Clearing ring of boxers ..."
  response=$(curl -s -X GET "$BASE_URL/clear-ring")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Ring cleared successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Ring JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to clear ring."
    exit 1
  fi
}

enter_ring() {
  boxer=$1

  echo "Boxer $boxer entering ring ..."
  curl -s -X POST "$BASE_URL/enter-ring" -H "Content-Type: application/json" \
    -d "{\"boxer\":\"$boxer\"}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Boxer entered ring successfully."
  else
    echo "Boxer failed to enter ring."
    exit 1
  fi
}

get_boxers_in_ring() {

  echo "Getting boxers in the ring ..."
  response=$(curl -s -X GET "$BASE_URL/ger-boxers-in-ring")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Got boxers from ring successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Boxers JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get boxers from ring."
    exit 1
  fi
}

#Health checks
check_health
check_db

#Create boxers
create_boxer "Boxer A" 150 71 72.2 21
create_boxer "Boxer B" 175 74 75.5 24
create_boxer "Boxer C" 180 70 71.5 22

#Delete boxer
delete_boxer_by_id 3

#Get boxers
get_boxer_by_id 1
get_boxer_by_name "Boxer A"

#Fight
enter_ring "Boxer A"
enter_ring "Boxer B"
get_boxers_in_ring
fight

#Leaderboard
get_leaderboard "wins"
get_leaderboard "win_pct"

#Clear ring
clear_ring

echo "All tests passed successfully!"