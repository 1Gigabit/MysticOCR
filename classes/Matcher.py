import ast
import difflib
from time import sleep

import requests

from classes.Card import Card, OCRCard
from classes.Database import Database
import concurrent.futures


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

    def create_workers(self):
        with concurrent.futures.ThreadPoolExecutor(8) as executor:
            futures = [
                executor.submit(process_chunk, chunk)
                for chunk in self.ocr_result_chunks
            ]

            for future in concurrent.futures.as_completed(futures):
                passed_cards, failed_cards = future.result()
                if passed_cards:
                    self.insert_passed_cards(passed_cards)
                if failed_cards:
                    self.insert_failed_cards(failed_cards)

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

    def search_with_local_db(self):
        with requests.Session() as session:
            for ocr_card in self.ocr_db_cards:
                ocr_data = ast.literal_eval(ocr_card.ocr_result)[:3]
                ocr_text = [data[1] for data in ocr_data]
                if len(ocr_text) != 0:
                    sleep(0.1)
                    response = session.get(
                        f"https://api.scryfall.com/cards/search?unique=prints&q='{ocr_text[0]}'"
                    )
                    if response.status_code == 200:
                        response_data = response.json().get("data")
                        smallest_card = get_lowest_priced_card(response_data)

                        if smallest_card:
                            print(
                                response_data[0].get("name"),
                                smallest_card["smallest_price"],
                            )
                            self.insert_passed_cards(
                                [create_proper_card(ocr_card, smallest_card)]
                            )

                    else:
                        print(ocr_text)
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
            cutoff=0.8,
        )
        if len(confirmed_card_name) != 0:
            confirmed_card_name = confirmed_card_name[0]
            cards = [
                card
                for card in self.card_set
                if card.get("name") == confirmed_card_name  # type: ignore
            ]
            smallest_card = get_lowest_priced_card(cards)
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


def get_lowest_priced_card(cards):
    filtered_cards = []
    for card in cards:
        prices = [
            card.get("prices").get("usd"),
            card.get("prices").get("usd_foil"),
            card.get("prices").get("eur"),
        ]
        filtered_prices = [float(price) for price in prices if price]
        if filtered_prices:
            smallest_price = min(filtered_prices)
            filtered_cards.append({"card": card, "smallest_price": smallest_price})
    filtered_cards.sort(key=lambda x: x.get("smallest_price"), reverse=False)
    return filtered_cards[0] if len(filtered_cards) >= 1 else None


def process_chunk(ocr_chunk: list[OCRCard]):
    failed_cards = []
    passed_cards = []
    for ocr_card in ocr_chunk:
        ocr_data = ast.literal_eval(ocr_card.ocr_result)[:3]
        ocr_text = [data[1] for data in ocr_data]
        if len(ocr_text) != 0:
            response = requests.get(
                f"https://api.scryfall.com/cards/search?unique=prints&q='{ocr_text[0]}'"
            )
            if response.status_code == 200:
                cards = response.json().get("data", [])
                filtered_cards = []
                for card in cards:
                    prices = [
                        card.get("prices").get("usd"),
                        card.get("prices").get("usd_foil"),
                        card.get("prices").get("eur"),
                    ]
                    filtered_prices = [float(price) for price in prices if price]
                    if filtered_prices:
                        smallest_price = min(filtered_prices)
                        filtered_cards.append(
                            {"card": card, "smallest_price": smallest_price}
                        )
                filtered_cards.sort(
                    key=lambda x: x.get("smallest_price"), reverse=False
                )
                if filtered_cards:
                    smallest_card = filtered_cards[0]
                    proper_smallest_card = {
                        "id": ocr_card.id,
                        "ratio": 0.0,
                        "card": smallest_card["card"],
                        "price": smallest_card["smallest_price"],
                        "foil": ocr_card.type,
                        "ocr": ocr_card.ocr_result,
                    }
                    smallest_card_name = proper_smallest_card["card"]["name"]
                    smallest_price = proper_smallest_card["price"]
                    # print(smallest_card_name, smallest_price)
                    passed_cards.append(proper_smallest_card)
            elif response.status_code == 404:
                print(f"FAILED TO SEARCH FOR {ocr_text}")
                failed_cards.append(
                    {
                        "id": ocr_card.id,
                        "card": ocr_card.file_name,
                        "ratio": 0.0,
                        "price": 0.0,
                        "foil": ocr_card.type,
                        "ocr": ocr_card.ocr_result,
                    }
                )
            return [passed_cards, failed_cards]
    return [None, None]
