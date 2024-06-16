import os
import sys
import argparse
import pefile


def delete_non_pe_files(directory):
    # Iterate over the files in the specified directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        # Skip directories
        if os.path.isdir(file_path):
            continue

        try:
            # Attempt to parse the file as a PE file
            pe = pefile.PE(file_path)
        except pefile.PEFormatError:
            # If a PEFormatError is raised, the file is not a PE file; delete it
            print(f"Deleting non-PE file: {file_path}")
            os.remove(file_path)
        except Exception as e:
            # Handle unexpected errors
            print(f"Error processing file {file_path}: {e}")
        else:
            # No error, so the file is a PE file
            print(f"Keeping PE file: {file_path}")


def main():
    parser = argparse.ArgumentParser(description='Delete non-PE files from a directory.')
    parser.add_argument('directory', type=str, help='The directory to scan and delete non-PE files from.')

    args = parser.parse_args()

    # Check if the provided directory path exists
    if not os.path.exists(args.directory):
        print(f"Error: The directory '{args.directory}' does not exist.")
        sys.exit(1)

    # Call the function to delete non-PE files
    delete_non_pe_files(args.directory)


if __name__ == "__main__":
    main()
