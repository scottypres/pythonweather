from flask import Flask, jsonify, request
from flask_cors import CORS
import requests, json

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes and all origins  

# This is a mock function for processing data that you would implement
def relabel_data(data):
    # Your processing logic goes here
    # For now, I'm just returning data as is
    relabeled_data = data
    return relabeled_data

@app.route('/query_external_api', methods=['GET'])
def query_external_api():
    external_api_url = 'http://192.168.1.145:5000/'
    try:
        response = requests.get(external_api_url)
        response.raise_for_status()
        data = response.json()  # Assuming the response will be in JSON format
        relabeled_data = relabel_data(data)
        return jsonify(relabeled_data)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# This route will serve the processed data to the HTML client
@app.route('/get_processed_data', methods=['GET'])
def get_processed_data():
    # Original function that returns a Flask Response object
    response = query_external_api()
    
    # Extract JSON data from the Response object
    if response.status_code == 200:
        processed_data = response.get_json()  # Use get_json() to get the data
        return jsonify(processed_data)
    else:
        return jsonify({"error": "Failed to get processed data"}), response.status_code

    
if __name__ == '__main__':
    app.run(debug=True)