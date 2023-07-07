import ast
import difflib
import psycopg2
import requests

from classes.Card import Card, OCRCard
from classes.Database import Database


class Matcher:
    config: dict
    card_set: list[Card]
    db: Database
    ocr_result_chunks: list[list[OCRCard]]
    ocr_db_cards: list[OCRCard]

    def __init__(self, config, card_set, db):
        self.config = config
        self.card_set = card_set
        self.db = db
        cursor = self.db.db_connection.cursor()
        cursor.execute("SELECT id, file_name, ocr_result, type,location FROM cards;")
        self.ocr_db_all = cursor.fetchall()
        self.ocr_db_cards: list[OCRCard] = []
        for ocr_card in self.ocr_db_all:
            self.ocr_db_cards.append(
                OCRCard(ocr_card[0], ocr_card[1], ocr_card[2], ocr_card[3], ocr_card[4])
            )

    def chunkify(self, chunk_size: int):
        self.ocr_result_chunks = [
            self.ocr_db_cards[i : i + chunk_size]
            for i in range(0, len(self.ocr_db_cards), chunk_size)
        ]

    def insert_passed_cards(self, passed_cards):
        cursor = self.db.db_connection.cursor()
        insert_query = "INSERT INTO match_results (ocr_id, name, ocr_result, price, foil, ratio) VALUES (%s, %s, %s, %s, %s, %s)"
        for passed_card in passed_cards:
            card_id = passed_card.get("id")
            card_name = passed_card.get("card").get("name")
            ocr_result = passed_card.get("ocr")
            card_price = passed_card.get("price")
            card_foil = passed_card.get("foil")
            card_ratio = passed_card.get("ratio")
            cursor.execute(
                insert_query,
                (card_id, card_name, ocr_result, card_price, card_foil, card_ratio),
            )
        self.db.db_connection.commit()

    def insert_failed_cards(self, failed_cards):
        cursor = self.db.db_connection.cursor()
        insert_query = "INSERT INTO failed_results (ocr_id, name, ocr_result, price, foil, ratio) VALUES (%s, %s, %s, %s, %s, %s)"
        for failed_card in failed_cards:
            card_id = failed_card["id"]
            card_name = failed_card.get("card")
            ocr_result = str(failed_card.get("ocr"))
            card_price = failed_card.get("price")
            card_foil = str(failed_card.get("foil"))
            card_ratio = failed_card.get("ratio")
            cursor.execute(
                insert_query,
                (card_id, card_name, ocr_result, card_price, card_foil, card_ratio),
            )
        self.db.db_connection.commit()

    def search_only_these_file_names(self, files):
        cursor: psycopg2.cursor = self.db.db_connection.cursor()
        for file in files:
            cursor.execute(f"SELECT * FROM cards WHERE file_name = '{file}'")
            result = cursor.fetchmany()[0]
            ocr_card = OCRCard(result[0], result[1], result[6], result[3], result[4])
            self.match_singular_card(ocr_card)

    def search_with_local_db(self):
        for ocr_card in self.ocr_db_cards:
            self.match_singular_card(ocr_card)

    def match_singular_card(self, ocr_card):
        ocr_data = ast.literal_eval(ocr_card.ocr_result)[:3]
        ocr_text = [data[1] for data in ocr_data]
        result = False
        for index in range(0, 3):
            result = self.secondary_match(ocr_text, ocr_card, index)
            if result:
                break
        if result is not True:
            print(f"COMPLETELY FAILED: {ocr_card.file_name}")
            self.insert_failed_cards(
                [
                    {
                        "id": ocr_card.id,
                        "card": ocr_card.file_name,
                        "ratio": 0.0,
                        "price": 0.0,
                        "foil": ocr_card.type,
                        "ocr": ocr_card.ocr_result,
                    }
                ]
            )

    def secondary_match(self, ocr_text, ocr_card, match_index):
        confirmed_card_name = difflib.get_close_matches(
            ocr_text[match_index],
            [card.get("name") for card in self.card_set],  # type: ignore
            n=3,
            cutoff=0.95,
        )
        if len(confirmed_card_name) != 0:
            confirmed_card_name = confirmed_card_name[0]
            cards = [
                card
                for card in self.card_set
                if card.get("name") == confirmed_card_name  # type: ignore
            ]
            smallest_card = get_lowest_priced_card(cards, ocr_card)
            if smallest_card is not None:
                print(f"Secondary match OK: {confirmed_card_name}")
                self.insert_passed_cards([create_proper_card(ocr_card, smallest_card)])
                return True
            print(f"Secondary match (NO PRICES) FAILED: {confirmed_card_name}")
            return False
        else:
            print(f"Secondary match FAILED: {ocr_text[match_index]}")
            return False


def create_proper_card(ocr_card, smallest_card):
    proper_smallest_card = {
        "id": ocr_card.id,
        "ratio": 0.0,
        "card": smallest_card["card"],
        "price": smallest_card["smallest_price"],
        "foil": ocr_card.type,
        "ocr": ocr_card.ocr_result,
    }
    return proper_smallest_card


def get_lowest_priced_card(cards, ocr_card: OCRCard):
    filtered_cards = []
    for card in cards:
        ocr_isFoiled = (
            True
            if ocr_card.type == "Foil"
            or ocr_card.type == "Borderless Foil"
            or ocr_card.type == "Foil Showcase"
            else False
        )
        is_both_foiled = False
        if card.get("foil") and ocr_isFoiled:
            is_both_foiled = True

        prices = [
            card.get("prices").get("usd") if is_both_foiled is not True else None,
            card.get("prices").get("usd_foil"),
        ]
        filtered_prices = [float(price) for price in prices if price]
        if filtered_prices:
            smallest_price = min(filtered_prices)
            filtered_cards.append({"card": card, "smallest_price": smallest_price})
        if filtered_cards:
            filtered_cards.sort(key=lambda x: x.get("smallest_price"), reverse=False)
    return filtered_cards[0] if len(filtered_cards) >= 1 else None
