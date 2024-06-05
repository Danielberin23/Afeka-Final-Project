import os
import math
import pefile
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from joblib import load
import numpy as np
import requests
import hashlib

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads/'

#prepare VirusTotal API:
api_key = 'f848319ea1cd5e2b44f7bc686ce99583662cfdd2904e6371543e685033786a39'
url = "https://www.virustotal.com/api/v3/files"
headers = {
    "accept": "application/json",
    "x-apikey": api_key,
}

# Load the model and the scaler
model_path = os.path.join('model', 'random_forest_model.joblib')
scaler_path = os.path.join('model', 'scaler.joblib')
model = load(model_path)
scaler = load(scaler_path)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

#analyze file against the machine learning model
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)  # Save the file to disk

    if not is_pe_file(file_path):
        os.remove(file_path)
        return jsonify({"error": "SUSPICIOUS FILE ALERT: File has an executable signature but an invalid PE header."}), 400

    # Analyze the PE file
    result = analyze_file(file_path)
    os.remove(file_path)
    return jsonify({"result": int(result)})


#Receive file on server, Attempt to get file report by signature, otherwise upload file for an active scan.
@app.route('/virusTotal', methods=['POST'])
def virusTotal():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Save the file temporarily to disk
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)  

    try:
        data = get_report_by_hash(file_path)

        if (data != None):
            return jsonify({"hash": data['data']}) #successful virusTotal file report by signature (md5 hash)

        with open(file_path, "rb") as f:
            files = {'file': (file.filename, f)}
            response = requests.post(url, headers=headers, files=files) #blocking function

        if response.status_code != 200:
            return jsonify({"error": "Failed to scan the file", "status": response.status_code}), response.status_code
        
        os.remove(file_path)
        data = response.json()
        return jsonify({"file_id": data['data']['id']}), 202

    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

            
#JS client repeatedly polls through requests to this function until the returned status is 'completed'
@app.route('/status/<file_id>', methods=['GET'])
def check_status(file_id):
    try:
        url_id = f"https://www.virustotal.com/api/v3/analyses/{file_id}"
        response = requests.get(url_id, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return jsonify(data)
        else:
            return jsonify({"error": f"Failed to get status. Status code: {response.status_code}"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

#attempts to get file report by file signature.
def get_report_by_hash(file_path):
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    md5_digest = md5_hash.hexdigest()

    urlbymd5 = f"https://www.virustotal.com/api/v3/files/{md5_digest}"
    response = requests.get(urlbymd5, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data
    return None

#checks if the uploaded file is a Portable Executable.
def is_pe_file(file_path):
    if not os.path.isfile(file_path):
        return False
    try:
        with open(file_path, 'rb') as f:
            pefile.PE(data=f.read())
        return True
    except Exception as e:
        print(f"Failed to validate PE file: {e}")
        return False


#calculates file entropy.
def shannon_entropy(data):
    freq = {}
    for byte in data:
        freq[byte] = freq.get(byte, 0) + 1
    total_bytes = len(data)
    entropy = -sum((count / total_bytes) * math.log2(count / total_bytes) for count in freq.values() if count != 0)
    return entropy


 # Calculate overall file entropy and extract PE features.
def analyze_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            file_content = file.read()
        file_size = os.path.getsize(file_path)
        entropy = shannon_entropy(file_content)
        pe = pefile.PE(file_path)
        features_array = np.array([
            entropy,
            file_size,
            len(pe.sections),
            pe.FILE_HEADER.TimeDateStamp,
            pe.FILE_HEADER.Characteristics,
            pe.OPTIONAL_HEADER.DllCharacteristics,
            len(pe.DIRECTORY_ENTRY_IMPORT) if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT') else 0,
            0 if pe.verify_checksum() else 1
        ]).reshape(1, -1)

        print("Features:", features_array)
        scaled_features_array = scaler.transform(features_array)
        print("Scaled Features:", scaled_features_array)
        prediction = model.predict(scaled_features_array)[0]
        return prediction
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return "Error processing file"



if __name__ == '__main__':
    app.run(debug=True)
