import os
import sys
import pefile
import csv
from collections import defaultdict


def count_imported_functions(directory, output_csv):
    # Dictionary to store the count of files importing each function
    function_count = defaultdict(int)

    # Iterate through all files in the given directory
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)

        try:
            # Attempt to load the PE file
            pe = pefile.PE(filepath)

            # Check if the PE file has imports
            if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
                # Iterate through each import entry
                for entry in pe.DIRECTORY_ENTRY_IMPORT:
                    for imp in entry.imports:
                        if imp.name is not None:
                            # Increment the count for this function
                            function_count[imp.name.decode()] += 1

        except OSError:
            # Skip files that are not PE files or are corrupted
            continue
        except pefile.PEFormatError:
            # Handle PE format errors
            continue

    # Sort the dictionary by count in descending order
    sorted_function_count = sorted(function_count.items(), key=lambda item: item[1], reverse=True)

    # Write the results to a CSV file
    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Function', 'Count'])
        for func, count in sorted_function_count:
            writer.writerow([func, count])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <directory> [output_csv_path]")
        sys.exit(1)

    # Directory to analyze
    directory = sys.argv[1]

    # CSV output path (optional argument)
    if len(sys.argv) > 2:
        output_csv = sys.argv[2]
    else:
        output_csv = 'imported_functions_count.csv'  # Default CSV file path

    count_imported_functions(directory, output_csv)
