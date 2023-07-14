import json
import os
import psycopg2
import requests
from datetime import date

import tqdm

from classes.Database import Database


class MysticPricer:
    db: Database

    def __init__(self, db) -> None:
        self.db = db

        pass

    def download_db(self):
        json = requests.get("https://api.scryfall.com/bulk-data/default-cards").json()
        if not os.path.exists(f"{date.today()}.json"):
            download_file(json)

    def open_card_set(self):
        with open(f"{date.today()}.json", encoding="utf-8") as f:
            return json.loads(f.read())

    def update_all_prices(self):
        card_set = self.open_card_set()
        cursor: psycopg2.cursor = self.db.db_connection.cursor()
        cursor.execute("SELECT ocr_id, name, price, foil FROM match_results")
        results = cursor.fetchall()
        for row in results:
            found_cards = []
            name = row[1]
            filtered_cards = []
            for card in card_set:
                if name == card.get("name"):
                    found_cards.append(card)
            for card in found_cards:
                ocr_isFoiled = (
                    True
                    if row[3] == "Foil"
                    or row[3] == "Borderless Foil"
                    or row[3] == "Foil Showcase"
                    else False
                )
                is_both_foiled = False
                if card.get("foil") and ocr_isFoiled:
                    is_both_foiled = True

                prices = [
                    card.get("prices").get("usd")
                    if is_both_foiled is not True
                    else None,
                    card.get("prices").get("usd_foil"),
                ]
                filtered_prices = [float(price) for price in prices if price]
                if filtered_prices:
                    smallest_price = min(filtered_prices)
                    filtered_cards.append(
                        {"card": card, "smallest_price": smallest_price}
                    )
                if filtered_cards:
                    filtered_cards.sort(
                        key=lambda x: x.get("smallest_price"), reverse=False
                    )

            if len(filtered_cards) >= 1:
                print(f"UPDATED CARD: {filtered_cards[0].get('card').get('name')}")
                cursor.execute(
                    "UPDATE match_results SET price = %s WHERE ocr_id = %s",
                    (filtered_cards[0].get("smallest_price"), row[0]),
                )
                self.db.db_connection.commit()


def download_file(json):
    with requests.get(json.get("download_uri"), stream=True) as r:
        with tqdm.tqdm(
            total=json.get("size"),
            unit="iB",
            unit_scale=True,
            desc="Downloading database",
        ) as pbar:
            r.raise_for_status()
            with open(f"{date.today()}.json", "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    pbar.update(len(chunk))
                    f.write(chunk)
