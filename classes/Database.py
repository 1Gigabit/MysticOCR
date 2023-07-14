import os
from typing import Any
import psycopg2
import tqdm
from .Card import OCRCard
from .Card import Card


class Database:
    config: dict
    db_connection: Any

    def __init__(self, config):
        self.config = config
        self.db_connection = psycopg2.connect(
            database="mysticocr",
            user="Chad",
            password="Dashwood",
            host="chadserver.local",
            port="5432",
        )
        ocr_cursor = self.db_connection.cursor()

        if config["overwrite_db"] == True and (
            config["command"] == "scan" or config["command"] == "scan_new"
        ):
            ocr_cursor.execute("DROP TABLE IF EXISTS match_results;")
            ocr_cursor.execute("DROP TABLE IF EXISTS failed_results;")
            ocr_cursor.execute("DROP TABLE IF EXISTS cards;")
        ocr_cursor.execute(
            "CREATE TABLE IF NOT EXISTS cards ( "
            + "id SERIAL PRIMARY KEY,"
            + "file_name            TEXT     ,"
            + "location             TEXT     ,"
            + "type TEXT,"
            + "date TEXT, "
            + "showcase             TEXT     ,"
            + "ocr_result           TEXT     ,"
            + "image                bytea   ,"
            + "borderless TEXT "
            + ");"
        )

        if config["overwrite_db"] == True and (
            config["command"] == "match" or config["command"] == "match_new"
        ):
            ocr_cursor.execute("DROP TABLE IF EXISTS failed_results;")
            ocr_cursor.execute("DROP TABLE IF EXISTS match_results;")
        ocr_cursor.execute(
            "CREATE TABLE IF NOT EXISTS match_results (  "
            + "ocr_id               INTEGER NOT NULL PRIMARY KEY  , "
            + "ratio                INTEGER     , "
            + "name                 TEXT     , "
            + "ocr_result TEXT,"
            + "price TEXT,"
            + "foil TEXT,"
            "FOREIGN KEY ( ocr_id ) REFERENCES cards( id ) " + ");"
        )

        ocr_cursor.execute(
            "CREATE TABLE IF NOT EXISTS failed_results (  "
            + "ocr_id               INTEGER NOT NULL PRIMARY KEY  , "
            + "ratio                INTEGER     , "
            + "name                 TEXT     , "
            + "ocr_result TEXT,"
            + "price FLOAT,"
            + "foil TEXT,"
            "FOREIGN KEY ( ocr_id ) REFERENCES cards( id ) " + ");"
        )
        self.db_connection.commit()
        return None

    def insert_ocr_result(self, file_path, ocr_result, original_imagecv):
        split_path = os.path.dirname(file_path).split("\\")
        location = split_path[3]
        type = split_path[4]
        date = split_path[5]
        self.db_connection.cursor().execute(
            "INSERT INTO cards(file_name,location,type,date,showcase,ocr_result) VALUES (%s,%s,%s,%s,%s,%s);",
            (
                file_path.replace("\\", "/"),
                location,
                type,
                date,
                self.config["scan"]["card"]["showcase"],
                f"{ocr_result}",
            ),
        )
        self.db_connection.commit()

    def import_card_for_set(self, cursor, card):
        card = Card(card)
        insert_sql = """
        INSERT INTO card_set (card_id,name,prices,foil) VALUES (%s,%s,%s,%s)
        """
        values = (card.id, card.name, f"{card.prices}", card.foil)

        cursor.execute(insert_sql, values)
        self.db_connection.commit()

    def import_card_set(self, card_db):
        cursor = self.db_connection.cursor()
        ##TODO ADD OVERWRITE CONFIG SUPPORT
        cursor.execute("DROP TABLE IF EXISTS card_set;")
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS card_set (
            id SERIAL PRIMARY KEY,
            card_id TEXT,
            name TEXT,
            prices TEXT,
            foil BOOLEAn);"""
        )
        self.db_connection.commit()
        cursor.execute("""SELECT * FROM card_set WHERE id=1;""")
        print("IMPORTING CARD SET JSON INTO DATABASE")
        if len(cursor.fetchall()) == 0:
            with tqdm.tqdm(card_db) as pbar:
                for card in card_db:
                    self.import_card_for_set(cursor, card)
                    pbar.update()

    def fetch_card_file_names(self):
        cursor: psycopg2.cursor = self.db_connection.cursor()
        cursor.execute("SELECT file_name FROM cards;")
        return cursor.fetchall()

    def fetch_unmatched_file_names(self):
        cursor: psycopg2.cursor = self.db_connection.cursor()
        cursor.execute(
            """SELECT file_name FROM cards
	LEFT JOIN match_results ON cards.id = match_results.ocr_id
	LEFT JOIN failed_results ON cards.id = failed_results.ocr_id
WHERE match_results.ocr_id is null and failed_results.ocr_id is null"""
        )
        return cursor.fetchall()

    def insert_passed_card(self, ocr_card: OCRCard, card: dict):
        cursor: psycopg2.cursor = self.db_connection.cursor()
        insert_query = "INSERT INTO match_results (ocr_id, name, ocr_result, price, foil) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(
            insert_query,
            (
                ocr_card.id,
                card.get("card", {}).get("name"),
                ocr_card.ocr_result,
                card.get("lowest_price"),
                ocr_card.type,
            ),
        )
        print(f"Inserting: {card.get('card',{}).get('name')}")
        self.db_connection.commit()

    def insert_failed_cards(self, failed_cards):
        cursor: psycopg2.cursor = self.db_connection.cursor()
        insert_query = "INSERT INTO failed_results (ocr_id, name, ocr_result, price, foil) VALUES (%s, %s, %s, %s, %s)"

        self.db_connection.commit()
