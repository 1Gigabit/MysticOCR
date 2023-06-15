from argparse import ArgumentParser
import ast
import csv
import json
from fuzzywuzzy import fuzz

args = ArgumentParser()
args.add_argument("-c", "--csv_file_path", help="Path to the CSV file", required=True)
args.add_argument("-db","--database_file_path", help="Path to the database file", required=True)
args.add_argument("-name","--name", help="Get names of cards from the CSV file", required=True)
def compare_csv_with_json(csv_file_path, json_file_path, threshold_ratio):
    # Load the JSON data from the JSON file
    with open(json_file_path, encoding="utf-8") as json_file:
        json_data = json.load(json_file)

    # Open the CSV file
    with open(csv_file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        # Iterate over each row in the CSV file
        for row in csv_reader:
            if(len(row) != 0):
                cellLiteral = ast.literal_eval(row[0])
                name = cellLiteral[1]
                print(name)
                


# Provide th   e file paths for the CSV and JSON files
csv_file_path = 'result.csv'
json_file_path = 'db.json'

# Set the threshold ratio for the match accuracy
threshold_ratio = 20  # Adjust this value based on your requirements

# Call the function to compare CSV with JSON
compare_csv_with_json(csv_file_path, json_file_path, threshold_ratio)
