import pandas as pd
import shutil
import os

# Load your dataset
df = pd.read_csv('D:/virus_folder/samples.csv')

# Define your source folder where all files are currently stored
source_folder = 'D:/virus_folder/bigdataset/samples'

# Define the destination folders
malware_folder = 'D:/virus_folder/bigdataset/mal'
benign_folder = 'D:/virus_folder/bigdataset/ben'

# Ensure destination folders exist
os.makedirs(malware_folder, exist_ok=True)
os.makedirs(benign_folder, exist_ok=True)

# Iterate over the dataset and move files accordingly
for index, row in df.iterrows():
    source_file = os.path.join(source_folder, str(row['id']))
    if row['list'] == "Blacklist":
        # This is malware
        destination_file = os.path.join(malware_folder, str(row['id']))
    else:
        # This is benign
        destination_file = os.path.join(benign_folder, str(row['id']))

    # Move the file
    if os.path.exists(source_file):
        shutil.move(source_file, destination_file)
    else:
        print(f"File {source_file} does not exist.")
