import csv
from collections import defaultdict


def compare_function_counts(csv_file1, csv_file2, output_csv):
    # Load the function counts from both CSV files
    def load_function_counts(filename):
        counts = defaultdict(int)
        with open(filename, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the header row
            for row in reader:
                if row:
                    function, count = row[0], int(row[1])
                    counts[function] = count
        return counts

    counts1 = load_function_counts(csv_file1)
    counts2 = load_function_counts(csv_file2)

    # Compare function counts and calculate percentage differences
    all_functions = set(counts1.keys()) | set(counts2.keys())
    results = []
    for func in all_functions:
        count1 = counts1[func]
        count2 = counts2[func]
        total = count1 + count2
        if total > 0:
            percent_difference = ((count1 - count2) / total) * 100
        else:
            percent_difference = 0  # To handle cases where both counts are zero

        # Append only if the percentage difference is negative
        if percent_difference < 0:
            results.append([func, count1, count2, percent_difference])

    # Sort results by the maximum count from either file, descending
    results.sort(key=lambda x: max(x[1], x[2]), reverse=True)

    # Write the results to the output CSV file
    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Function', 'Count in File 1', 'Count in File 2', 'Percentage Difference'])
        for result in results:
            writer.writerow(result)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python script.py <csv_file1> <csv_file2> <output_csv>")
        sys.exit(1)

    compare_function_counts(sys.argv[1], sys.argv[2], sys.argv[3])
