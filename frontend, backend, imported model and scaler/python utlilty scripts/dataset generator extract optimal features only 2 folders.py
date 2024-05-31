import sys
import os
import math
import csv
import pefile

def shannon_entropy(data):
    """ Calculate the Shannon entropy of a block of data. """
    freq = {}
    for byte in data:
        freq[byte] = freq.get(byte, 0) + 1
    total_bytes = len(data)
    probabilities = [count / total_bytes for count in freq.values()]
    entropy = -sum(p * math.log2(p) for p in probabilities if p != 0)
    return entropy

def pe_features(filename):
    """ Extract various features from the PE file, returning None for critical failures. """
    # Initialize all attributes to None
    number_of_sections = None
    time_date_stamp = None
    characteristics = None
    dll_characteristics = None
    checksum_invalid = None
    import_count = 0

    try:
        pe = pefile.PE(filename)
        number_of_sections = len(pe.sections)
        time_date_stamp = pe.FILE_HEADER.TimeDateStamp
        characteristics = pe.FILE_HEADER.Characteristics
        dll_characteristics = pe.OPTIONAL_HEADER.DllCharacteristics
        checksum_invalid = 0 if pe.verify_checksum() else 1
        if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
            import_count = sum(len(dll.imports) for dll in pe.DIRECTORY_ENTRY_IMPORT if hasattr(dll, 'imports'))
    except pefile.PEFormatError as e:
        print(f"Skipping file {filename} due to invalid NT headers: {e}")
        return None  # Critical failure, skip this file entirely
    except Exception as e:
        print(f"Non-critical error processing file {filename}: {e}")
        # Return with some attributes potentially set to None
        return (number_of_sections, time_date_stamp, characteristics, dll_characteristics, import_count, checksum_invalid)

    return (number_of_sections, time_date_stamp, characteristics, dll_characteristics, import_count, checksum_invalid)

def calculate_entropy_and_pe_features(filename):
    """ Calculate overall file entropy and extract PE features, handling files based on error type. """
    with open(filename, 'rb') as file:
        file_content = file.read()
    file_size = os.path.getsize(filename)
    entropy = shannon_entropy(file_content)
    pe_result = pe_features(filename)
    if pe_result is None:
        return None  # Skip this file completely if pe_features returned None
    return (entropy, file_size) + pe_result

def calculate_features_for_folder(folder_path, output_file, malware_label):
    """ Process each file in a folder and record their features to a CSV, handling errors appropriately. """
    with open(output_file, 'a', newline='') as csvfile:
        fieldnames = ['malware', 'entropy', 'length', 'number_of_sections', 'time_date_stamp',
                      'characteristics', 'dll_characteristics', 'import_count', 'checksum_invalid']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                features = calculate_entropy_and_pe_features(file_path)
                if features is not None:
                    row = dict(zip(fieldnames, [malware_label] + list(features)))
                    writer.writerow(row)

def main():
    """ Main function to handle command line arguments and process folders. """
    if len(sys.argv) != 4:
        print("Usage: python script.py <benign_folder> <malicious_folder> <output_file>")
        sys.exit(1)

    benign_folder = sys.argv[1]
    malicious_folder = sys.argv[2]
    output_file = sys.argv[3]

    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['malware', 'entropy', 'length', 'number_of_sections', 'time_date_stamp',
                      'characteristics', 'dll_characteristics', 'import_count', 'checksum_invalid']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    calculate_features_for_folder(benign_folder, output_file, 0)  # Benign files
    calculate_features_for_folder(malicious_folder, output_file, 1)  # Malicious files

if __name__ == "__main__":
    main()
