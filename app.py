import os
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
import pytz
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Load Date Time


# MongoDB Atlas Configuration with improved connection handling
def get_database():
    """
    Establish and return a MongoDB database connection
    """
    try:
        # Parse connection string
        connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        
        if not connection_string:
            raise ValueError("MongoDB connection string is not set in .env file")
        
        # Create a MongoClient
        client = MongoClient(connection_string)
        
        # Extract database name from connection string
        url_parts = connection_string.split('/')
        database_name = url_parts[-1].split('?')[0] if len(url_parts) > 3 else 'test'
        
        # Get the database
        db = client[database_name]
        
        print(f"Successfully connected to database: {database_name}")
        return db
    
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

# Initialize database
db = get_database()

# Check if database connection was successful
if db is None:
    raise Exception("Failed to connect to MongoDB. Please check your connection string.")

# Get locations collection
locations_collection = db.locations

def reverse_geocode(latitude, longitude):
    """
    Perform reverse geocoding to get address details
    Uses OpenStreetMap Nominatim API
    """
    try:
        # OpenStreetMap Nominatim API for reverse geocoding
        url = f"https://nominatim.openstreetmap.org/reverse"
        params = {
            'format': 'json',
            'lat': latitude,
            'lon': longitude,
            'zoom': 18,
            'addressdetails': 1
        }
        
        # Add User-Agent as per Nominatim Usage Policy
        headers = {
            'User-Agent': 'LocationTrackerApp/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant address components
            address = data.get('display_name', 'Unknown Location')
            
            # Try to extract more structured address details
            address_details = data.get('address', {})
            structured_address = {
                'display_name': address,
                'road': address_details.get('road', ''),
                'city': address_details.get('city', ''),
                'county': address_details.get('county', ''),
                'state': address_details.get('state', ''),
                'country': address_details.get('country', ''),
                'postcode': address_details.get('postcode', '')
            }
            
            return structured_address
        else:
            return {
                'display_name': 'Unable to retrieve location details',
                'raw_response': response.text
            }
    
    except Exception as e:
        return {
            'display_name': 'Geocoding error',
            'error': str(e)
        }

@app.route('/')
def index():
    """Render the main PWA page"""
    return render_template('index.html')

@app.route('/save-location', methods=['POST'])
def save_location():
    """
    Endpoint to save location data to MongoDB
    Expects JSON with latitude, longitude
    Performs reverse geocoding to get address details
    """
    data = request.get_json()
    
    # Extract location coordinates
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    # Perform reverse geocoding
    location_details = reverse_geocode(latitude, longitude)
    
        
    location_entry = {
        'latitude': latitude,
        'longitude': longitude,
        'timestamp': datetime.now(pytz.UTC).astimezone(pytz.timezone('Asia/Manila')),
        'device_id': data.get('device_id', 'unknown'),
        'location_details': location_details
    }
    print(location_entry)
    try:
        result = locations_collection.insert_one(location_entry)
        return jsonify({
            'status': 'success', 
            'message': 'Location saved',
            'location_details': location_details,
            'inserted_id': str(result.inserted_id)
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500

@app.route('/get-locations', methods=['GET'])
def get_locations():
    """
    Retrieve recent location entries
    Supports optional filtering by device_id
    """
    device_id = request.args.get('device_id', 'unknown')
    locations = list(locations_collection.find({
        'device_id': device_id
    }).sort('timestamp', -1).limit(50))
    
    # Convert ObjectId to string for JSON serialization
    for location in locations:
        location['_id'] = str(location['_id'])
        location['timestamp'] = location['timestamp'].isoformat()
    
    return jsonify(locations), 200

# Service Worker and Manifest routes
@app.route('/service-worker.js')
def service_worker():
    return app.send_static_file('service-worker.js')

@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
