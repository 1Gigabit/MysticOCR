import argparse
import json
import sqlite3

parser = argparse.ArgumentParser(description="Converts scryfall database (only the name key) to sqlite database",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-i", "--input-file", required=True)
parser.add_argument("-o", "--output-file", required=True)
args = parser.parse_args()


def create_table(cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS data
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT)''')


def insert_data(cursor, name):
    cursor.execute('''INSERT INTO data (name) VALUES (?)''', (name,))


def convert_json_to_sqlite(json_file, sqlite_file):

    with open(json_file, 'r', encoding="utf-8") as file:
        data = json.load(file)

    connection = sqlite3.connect(sqlite_file)
    cursor = connection.cursor()

    create_table(cursor)

    for item in data:
        name = item.get('name')
        if name:
            insert_data(cursor, name)

    connection.commit()
    connection.close()


convert_json_to_sqlite(args.input_file, args.output_file)
