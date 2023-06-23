from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
import ast
import csv
import itertools
import json
import os
import sqlite3
import sys
import threading
import time
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
    cursor.execute('DROP TABLE IF EXISTS "matched data"')
    cursor.execute('''CREATE TABLE IF NOT EXISTS 'matched data'
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      'card name' TEXT, 'matched' TEXT, 'ratio' INTEGER, 'file' TEXT)''')
    cursor.execute("SELECT name FROM data")

    # Open the CSV file
    with open(args.csv_file, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        next(csv_reader)  # Skip the header row

        done = False
        count = 0

        def animated_loading():
            for c in itertools.cycle(['|', '/', '-', '\\']):
                if done:
                    break
                sys.stdout.write(
                    f'\rSearching database  {c}  Working on line {count}')
                sys.stdout.flush()

                time.sleep(0.05)
            sys.stdout.write('\rDone!             ')
        t = threading.Thread(target=animated_loading, daemon=True)
        t.start()
        cards = cursor.fetchall()

        # Iterate over each row in the CSV file
        for row in csv_reader:
            count += 1
            if len(row) >= 1:
                highest_ratio = 0
                image_text = ""
                db_text = ""
                image_text = ast.literal_eval(row[0])
                if isinstance(image_text, int):
                    break
                if (image_text is int):
                    break
                for card in cards:

                    comparison = card[0] or ""
                    current_ratio = fuzz.ratio(
                        image_text[1], comparison)
                    if current_ratio > highest_ratio:
                        highest_ratio = current_ratio
                        db_text = comparison
                    if comparison.find("//") != -1 and comparison.find(image_text[1]) != -1:
                        highest_ratio = current_ratio
                        db_text = comparison
                        print(image_text, comparison)
                        break
                    if current_ratio == 100:
                        break
                cursor.execute(
                    "INSERT INTO 'matched data' ('card name', matched, ratio,file) VALUES (?,?,?,?)", (str(image_text[1]), str(db_text), int(highest_ratio), str(row[len(row)-1])))
                conn.commit()
        done = True


if __name__ == '__main__':
    main()
