from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
import ast
import csv
import json
import sqlite3
from fuzzywuzzy import fuzz
# Define the command-line arguments
parser = ArgumentParser(description="Similarity matcher for magic cards",
                        formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-c", "--csv_file",
                    help="Path to the CSV file", required=True)
parser.add_argument("-db", "--database_file",
                    help="Path to the database file", required=True)

args = parser.parse_args()


def main():
    # Load the JSON data from the JSON file
    conn = sqlite3.connect(args.database_file)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM data")

    # Open the CSV file
    with open(args.csv_file, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        next(csv_reader)  # Skip the header row

        # Iterate over each row in the CSV file
        cards = cursor.fetchall()
        for row in csv_reader:
            if len(row) >= 1:
                highest_ratio = 0
                image_text = ""
                db_text = ""
                row_literal = ast.literal_eval(row[0])
                if isinstance(row_literal, int):
                    break
                if(row_literal is int):
                    break
                for card in cards:

                    comparison = card[0] or ""
                    current_ratio = fuzz.ratio(
                        row_literal[1], comparison)
                    if current_ratio > highest_ratio:
                        highest_ratio = current_ratio
                        image_text = row_literal
                        db_text = comparison

                    if comparison.find("//") != -1 and comparison.find(row_literal[1]) != -1:
                        break
                    if current_ratio == 100:
                        break

                print(f'{highest_ratio}%  :  {image_text}  :  {db_text}')


if __name__ == '__main__':
    main()
