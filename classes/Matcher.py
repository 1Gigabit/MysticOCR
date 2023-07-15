import ast
from asyncio import as_completed
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures
import difflib
import psycopg2

from classes.Card import OCRCard
from classes.Database import Database


class Matcher:
    config: dict
    card_set: dict
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
        return [
            self.ocr_db_cards[i : i + chunk_size]
            for i in range(0, len(self.ocr_db_cards), chunk_size)
        ]

    def search_only_these_file_names(self, files):
        cursor: psycopg2.cursor = self.db.db_connection.cursor()
        for file in files:
            cursor.execute(f"SELECT * FROM cards WHERE file_name = '{file}'")
            result = cursor.fetchmany()[0]
            ocr_card = OCRCard(result[0], result[1], result[6], result[3], result[4])
            match_single_card(self.card_set, ocr_card)

    def search_with_local_db(self):
        for card in self.ocr_db_all:
            # Match each card from the local database
            ocr_card = OCRCard(card[0], card[1], card[2], card[3], card[4])
            matched_card = match_single_card(self.card_set, ocr_card)
            if matched_card != None:
                self.db.insert_passed_card(ocr_card, matched_card)

    def search_multi(self):
        chunks = self.chunkify(10)
        with ProcessPoolExecutor(max_workers=12) as executor:
            futures = []
            for chunk in chunks:
                futures.append(executor.submit(match_chunk, self.card_set, chunk))
            for future in concurrent.futures.as_completed(futures):
                results = future.result()
                for result in results:
                    self.db.insert_passed_card(
                        result.get("ocr_card"), result.get("matched_card")
                    )

    # Matches a single card to the local database


def match_chunk(card_set, chunk):
    passed_cards = []
    for ocr_card in chunk:
        # Match each card from the local database

        matched_card = match_single_card(card_set, ocr_card)
        if matched_card != None:
            passed_cards.append({"ocr_card": ocr_card, "matched_card": matched_card})
    return passed_cards


def match_single_card(card_set, ocr_card: OCRCard):
    ocr_text = [data[1] for data in ast.literal_eval(ocr_card.ocr_result)[:3]]
    for index in range(1, 3):
        # Find close matches of the OCR text with card names in the card set
        ocr_text_joined = " ".join(ocr_text[:index])
        card_names = [card.get("name").split("//")[0] for card in card_set]
        matched_card_names = difflib.get_close_matches(
            ocr_text_joined,
            card_names,  # type: ignore
            n=3,
            cutoff=0.85,
        )
        if len(matched_card_names) > 0:
            # Find all cards that matches the OCR text with the card names
            matched_cards = [
                card
                for card in card_set
                if card.get("name").split("//")[0] == matched_card_names[0]
            ]
            # Get the lowest priced card from the matched cards
            return get_lowest_priced_card(
                matched_cards, True if "foil" in ocr_card.type else False
            )


def get_lowest_priced_card(cards, foil) -> dict | None:
    filtered_cards = []
    for card in cards:
        prices = [
            card.get("prices", {}).get("usd") if foil else None,
            card.get("prices", {}).get("usd_foil"),
        ]
        filtered_prices = [float(price) for price in prices if price is not None]
        if filtered_prices:
            smallest_price = min(filtered_prices)
            filtered_cards.append({"card": card, "smallest_price": smallest_price})

    filtered_cards.sort(key=lambda x: x["smallest_price"])
    return filtered_cards[0] if filtered_cards else None
