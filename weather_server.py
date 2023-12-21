from flask import Flask, jsonify
from flask_cors import CORS
import requests
import json
import os
import time

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

FILENAME = 'processed_data.json'
TIMEOUT_FILE = 'last_update_time.txt'  # New file to track the timestamp of the last API call
API_TIMEOUT_SECONDS = 30 * 60 # 30 minutes in seconds
EXTERNAL_API_URL = 'http://192.168.1.145:5000/'  # You must define this if it's needed


# This is a mock function for processing data that you would implement
def relabel_data(data):
    relabeled_data = {}

    height_mapping = {
        '10m': '32ft',
        '80m': '262ft',
        '180m': '590ft',
    }
    
    pressure_mapping = {
        '1000hPa': '361ft',
        '975hPa': '1050ft',
        '950hPa': '1640ft',
        '925hPa': '2625ft',
        '900hPa': '3281ft',
        '850hPa': '4921ft',
        '800hPa': '6234ft',
    }

    # Debug: Print the input data
    print("Input data:", data)

    for key, value in data.items():
        # Debug: Print the current key being checked
        print("Checking key:", key) 

        found_matching_key = False
        # Check for height keys and replace them
        for original, replacement in height_mapping.items():
            if original in key:
                new_key = key.replace(original, replacement)
                relabeled_data[new_key] = value

                # Debug: Print the matching key information
                print(f"Found key matching height ({original}). Relabeled to {new_key}")

                found_matching_key = True
                break

        if not found_matching_key:
            # check for pressure keys if height keys are not present
            for original, replacement in pressure_mapping.items():
                if original in key:
                    new_key = key.replace(original, replacement)
                    relabeled_data[new_key] = value

                    # Debug: Print the matching key information
                    print(f"Found key matching pressure ({original}). Relabeled to {new_key}")

                    found_matching_key = True
                    break

        if not found_matching_key:
            # if neither height nor pressure keys are found, just copy the key-value pair
            relabeled_data[key] = value
            # Debug: Print message indicating no relabeling occurred
            print(f"No matching key for relabeling. Key '{key}' remains the same.")

    # Debug: Print the output data
    print("Relabeled data:", relabeled_data)

    return relabeled_data



@app.route('/query_external_api', methods=['GET'])
def query_external_api():
    try:
        response = requests.get(EXTERNAL_API_URL)
        response.raise_for_status()  # This will raise an exception for HTTP errors
        data = response.json()  # Assuming the response will be in JSON format
        
        relabeled_data = relabel_data(data)  # Call the relabeling function

        # Write relabeled data to FILENAME
        with open(FILENAME, 'w') as json_file:
            json.dump(relabeled_data, json_file, indent=4)

        # After successfully updating the data, write the current timestamp to TIMEOUT_FILE
        with open(TIMEOUT_FILE, 'w') as time_file:
            time_file.write(str(int(time.time())))

        return jsonify(relabeled_data)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
@app.route('/get_processed_data', methods=['GET'])
def get_processed_data():
    current_time = int(time.time())

    # Check if we have a last updated timestamp and if the data is older than 30 minutes
    if os.path.exists(TIMEOUT_FILE):
        with open(TIMEOUT_FILE, 'r') as time_file:
            last_update_time = int(time_file.read())
            if current_time - last_update_time > API_TIMEOUT_SECONDS:
                return query_external_api()  # Refresh data if more than 30 min old
    else:
        # Data has never been fetched, we need to fetch it
        return query_external_api()

    # The data is fresh (less than 30 minutes old), return it
    if os.path.exists(FILENAME):
        with open(FILENAME, 'r') as json_file:
            processed_data = json.load(json_file)
        return jsonify(processed_data)
    else:
        return jsonify({"error": "Processed data not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)