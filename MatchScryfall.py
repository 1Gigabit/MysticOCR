from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
import ast
import csv
import json
from fuzzywuzzy import fuzz
# Define the command-line arguments
parser = ArgumentParser(description="Similarity matcher for magic cards",
                        formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-c", "--csv_file_path",
                    help="Path to the CSV file", required=True)
parser.add_argument("-db", "--database_file_path",
                    help="Path to the database file", required=True)

args = parser.parse_args()


def main():
    # Load the JSON data from the JSON file
    try:
        with open(args.database_file_path, 'r', encoding="utf-8") as json_file:
            json_data = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading JSON file: {e}")
        return
    # Open the CSV file
    with open(args.csv_file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        next(csv_reader)  # Skip the header row

        # Iterate over each row in the CSV file
        for row in csv_reader:
            if len(row) >= 1:
                highest_ratio = 0
                current_match = ""
                for card in json_data:
                    row_literal = ast.literal_eval(row[0])
                    if isinstance(row_literal, int):
                        break
                    if(row_literal is int):
                        break
                    current_compare = card.get("name")
                    current_ratio = fuzz. ratio(
                        row_literal[1], current_compare)
                    if current_ratio > highest_ratio:
                        highest_ratio = current_ratio
                        current_match = current_compare
                    if current_ratio == 100:
                        break
                print(highest_ratio, current_match)


if __name__ == '__main__':
    main()
