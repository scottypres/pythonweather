from flask import Flask, jsonify
from flask_cors import CORS
import requests, json, os, time, re


app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

FILENAME = 'processed_data.json'
TIMEOUT_FILE = 'last_update_time.txt'  # New file to track the timestamp of the last API call
API_TIMEOUT_SECONDS = 1 # 30 minutes in seconds
EXTERNAL_API_URL = 'http://192.168.1.145:5000/'  # You must define this if it's needed

# Define your mappings outside of the relabel_data function so they can be accessed by relabel_item
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

# This is your relabel_data function, which includes the relabel_item function

def replace_keys(original_key, mapping):
    for key, value in mapping.items():
        original_key = original_key.replace(key, value)
    return original_key

def relabel_data(data):
    # Combine both mappings for easier iteration
    combined_mapping = {**height_mapping, **pressure_mapping}

    # Check if 'hourly_units' exist in data and is a dictionary
    if 'hourly_units' in data and isinstance(data['hourly_units'], dict):
        for original_key in list(data['hourly_units'].keys()):  # Make a copy of the keys
            new_key = replace_keys(original_key, combined_mapping)
            if new_key != original_key:  # Only change key if it's different
                data['hourly_units'][new_key] = data['hourly_units'].pop(original_key)

    # Check if 'hourly' exist in data and is a dictionary
    if 'hourly' in data and isinstance(data['hourly'], dict):
        for original_key in list(data['hourly'].keys()):  # Make a copy of the keys
            new_key = replace_keys(original_key, combined_mapping)
            if new_key != original_key:  # Only change key if it's different
                data['hourly'][new_key] = data['hourly'].pop(original_key)

    return data


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