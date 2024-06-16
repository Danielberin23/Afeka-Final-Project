import sys
import os
import csv
import pefile

# List of known good section names as byte strings
normal_section_names = [b'.text', b'.rdata', b'.data', b'.pdata', b'.rsrc', b'.idata', b'.bss', b'.code', b'.edata']

def shannon_entropy(data):
    """Calculate the Shannon entropy of a block of data."""
    from math import log2
    freq = {}
    for byte in data:
        freq[byte] = freq.get(byte, 0) + 1
    total_bytes = len(data)
    probabilities = [float(count) / total_bytes for count in freq.values()]
    entropy = -sum(p * log2(p) for p in probabilities if p != 0)
    return entropy

def section_name_checker(section_names):
    """Check section names against a list of known good names, working with byte strings."""
    number_of_suspicious_names = 0
    number_of_nonsuspicious_names = 0
    for name in section_names:
        if name.strip(b'\x00') in normal_section_names:
            number_of_nonsuspicious_names += 1
        else:
            number_of_suspicious_names += 1
    return number_of_suspicious_names, number_of_nonsuspicious_names

def pe_features(filename):
    """Extract various features from the PE file, adjusted for byte string handling."""
    # Initialize all values to None
    number_of_sections = None
    time_date_stamp = None
    characteristics = None
    major_image_version = None
    dll_characteristics = None
    checksum_invalid = None
    size_of_uninitialized_data = None
    size_of_initialized_data = None
    section_names = None
    text_section_entropy = None
    suspicious = None
    nonsuspicious = None
    dll_count = None
    import_count = 0

    try:
        pe = pefile.PE(filename)
        number_of_sections = len(pe.sections)
        time_date_stamp = pe.FILE_HEADER.TimeDateStamp
        characteristics = pe.FILE_HEADER.Characteristics
        major_image_version = pe.OPTIONAL_HEADER.MajorImageVersion
        dll_characteristics = pe.OPTIONAL_HEADER.DllCharacteristics
        checksum_invalid = 0 if pe.verify_checksum() else 1
        size_of_uninitialized_data = pe.OPTIONAL_HEADER.SizeOfUninitializedData
        size_of_initialized_data = pe.OPTIONAL_HEADER.SizeOfInitializedData

        section_names = [section.Name for section in pe.sections]
        suspicious, nonsuspicious = section_name_checker(section_names)

        text_section_entropy = None
        for section in pe.sections:
            if b'.text' in section.Name:
                text_section_entropy = section.get_entropy()
                break

        dll_count = len(pe.DIRECTORY_ENTRY_IMPORT) if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT') else 0
        import_count = sum(len(dll.imports) for dll in pe.DIRECTORY_ENTRY_IMPORT if hasattr(dll, 'imports')) if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT') else 0
    except pefile.PEFormatError as e:
        print(f"Skipping file {filename} due to invalid NT headers: {e}")
        return None
    except Exception as e:
        print(f"Error processing file {filename}: {e}")
        # Return initialized values, allowing other columns to be filled with None
        return (number_of_sections, time_date_stamp, characteristics, major_image_version, dll_characteristics, dll_count, import_count, checksum_invalid, text_section_entropy, suspicious, nonsuspicious, size_of_uninitialized_data, size_of_initialized_data)

    return (number_of_sections, time_date_stamp, characteristics, major_image_version, dll_characteristics, dll_count, import_count, checksum_invalid, text_section_entropy, suspicious, nonsuspicious, size_of_uninitialized_data, size_of_initialized_data)

def calculate_entropy_and_pe_features(filename):
    """Calculate overall file entropy and extract PE features, handling cases where PE extraction fails."""
    with open(filename, 'rb') as file:
        file_content = file.read()
    file_size = os.path.getsize(filename)
    entropy = shannon_entropy(file_content)
    pe_result = pe_features(filename)
    if pe_result is None:  # Check if pe_features returned None and handle it
        return None  # Return None to signal that this file should be skipped
    return (entropy, file_size) + pe_result  # Only concatenate if pe_result is not None


def calculate_features_for_folder(folder_path, malware_label, writer, fieldnames):
    """Process each file in a folder and record their features to a CSV."""
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            features = calculate_entropy_and_pe_features(file_path)
            if features is not None:  # Only write rows for successfully processed files or those with recoverable errors
                row = dict(zip(fieldnames, [malware_label] + list(features)))
                writer.writerow(row)


def main():
    """Main function to handle command line arguments and process folders."""
    if len(sys.argv) != 4:
        print("Usage: python script.py <benign_folder> <malicious_folder> <output_file>")
        sys.exit(1)

    benign_folder = sys.argv[1]
    malicious_folder = sys.argv[2]
    output_file = sys.argv[3]

    fieldnames = ['malware', 'entropy', 'length', 'number_of_sections', 'time_date_stamp',
                  'characteristics', 'major_image_version', 'dll_characteristics', 'dll_count',
                  'import_count', 'checksum_invalid', 'text_section_entropy', 'suspicious_section_names',
                  'nonsuspicious_section_names', 'size_of_uninitialized_data', 'size_of_initialized_data']

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        calculate_features_for_folder(benign_folder, 0, writer, fieldnames)  # Process benign files
        calculate_features_for_folder(malicious_folder, 1, writer, fieldnames)  # Process malicious files

if __name__ == "__main__":
    main()
