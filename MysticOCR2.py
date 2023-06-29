import ast
import glob
import json
import os
from re import split
import sqlite3
import sys
import cv2
import easyocr
import psycopg2
from regex import F
import yaml
from fuzzywuzzy import fuzz
import concurrent.futures

config = yaml.load(open('mysticocr.yml', 'r'),
                   Loader=yaml.FullLoader)['mystic']


def main():
    reader = easyocr.Reader(['en'])

    ocr_db = init_db()

    reader = easyocr.Reader(['en'], gpu=config['scan']['gpu'])
    # files = glob.glob(os.path.join(
    #     config['scan']['image_dir'], "*.jpg"), recursive=True)
    files = glob.glob(os.path.join(
        config['scan']['image_dir'], "**/*.jpg"), recursive=True)

    if config['command'] == 'scan':
        for file in files:
            ocr_result, imagecv = scan_file(reader, file)
            if (config['scan']['show_image']):
                show_image(imagecv, ocr_result)
            insert_ocr_result(ocr_db, file, ocr_result, imagecv)
    if config['command'] == 'match':

        card_db: list = json.loads(
            open(config['match']['card_db'], 'r', encoding='utf-8').read())
        match(card_db, ocr_db)


def init_db():
    conn = psycopg2.connect(database="mysticocr", user="Chad",
                            password="Dashwood", host="localhost", port="5432")
    ocr_cursor = conn.cursor()

    if (config['overwrite_db'] == True and config['command'] == "scan"):
        ocr_cursor.execute("DROP TABLE IF EXISTS match_results;")
        ocr_cursor.execute("DROP TABLE IF EXISTS cards;")
    ocr_cursor.execute(
        "CREATE TABLE IF NOT EXISTS cards ( " +
        "id SERIAL PRIMARY KEY," +
        "file_name            TEXT     ," +
        "location             TEXT     ," +
        "type TEXT," +
        "date TEXT, " +
        "showcase             TEXT     ," +
        "ocr_result           TEXT     ," +
        "image                bytea   ," +
        "borderless TEXT " +
        ");")

    if config['overwrite_db'] == True and config['command'] == "match":
        ocr_cursor.execute("DROP TABLE IF EXISTS failed_results;")
        ocr_cursor.execute("DROP TABLE IF EXISTS match_results;")
    ocr_cursor.execute("CREATE TABLE IF NOT EXISTS match_results (  " +
                       "ocr_id               INTEGER NOT NULL PRIMARY KEY  , " +
                       "ratio                INTEGER     , " +
                       "name                 TEXT     , " +
                       "ocr_result TEXT," +
                       "price TEXT," +
                       "foil TEXT,"
                       "FOREIGN KEY ( ocr_id ) REFERENCES cards( id ) " +
                       ");")

    ocr_cursor.execute("CREATE TABLE IF NOT EXISTS failed_results (  " +
                       "ocr_id               INTEGER NOT NULL PRIMARY KEY  , " +
                       "ratio                INTEGER     , " +
                       "name                 TEXT     , " +
                       "ocr_result TEXT," +
                       "price TEXT," +
                       "foil TEXT,"
                       "FOREIGN KEY ( ocr_id ) REFERENCES cards( id ) " +
                       ");")
    conn.commit()
    return conn


def scan_file(reader, file_path):
    originaL_imagecv = cv2.imread(file_path)
    image = originaL_imagecv.copy()
    if (config['scan']['card']['sideways']):
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    ocr_result = reader.readtext(
        image, width_ths=config['scan']['width_ths'], x_ths=config['scan']['x_ths'], batch_size=400)

    return [ocr_result, originaL_imagecv]


def show_image(image, ocr_result):
    for bbox in ocr_result:
        # Unpack the bounding box
        tl, tr, br, bl = bbox[0]
        tl = (int(tl[0]), int(tl[1]))
        tr = (int(tr[0]), int(tr[1]))
        br = (int(br[0]), int(br[1]))
        bl = (int(bl[0]), int(bl[1]))
        cv2.rectangle(image, tl, br, (10, 255, 0), 10)  # type: ignore
    cv2.imshow('Image', image)
    cv2.waitKey(1)


def insert_ocr_result(ocr_db, file_path, ocr_result, original_imagecv):
    split_path = os.path.dirname(file_path).split("\\")
    location = split_path[2]
    type = split_path[3]
    date = split_path[4]
    ocr_db.cursor().execute(
        "INSERT INTO cards(file_name,location,type,date,showcase,ocr_result,image) VALUES (%s,%s,%s,%s,%s,%s,%s);",
        (file_path, location, type, date, config['scan']['card']['showcase'], f'{ocr_result}', sqlite3.Binary(cv2.imencode(".jpg", original_imagecv)[1].tobytes())))
    ocr_db.commit()


def match_card(card_set, chunk):

    count = 0
    length = len(chunk)
    failed_cards = []
    passed_cards = []
    for ocr_result in chunk:
        count += 1
        highest_ratio = 0
        highest_card = {
            'id': ocr_result[0],
            'ratio': 0,
            'card': {
                'foil': False},
            'ocr': {},
        }

        ocr_text = []
        ocr_data = ast.literal_eval(ocr_result[2])
        for i in range(min(3, len(ocr_data))):
            ocr_text.append(ocr_data[i][1])
        for card in card_set:
            fuzzy_ratios = []
            comparison = ""
            card_isFoil = card.get('foil')
            ocr_isFoil = True if ocr_result[3] == "Foil" else False
            if (card_isFoil != ocr_isFoil):
                continue
            for ocr_word in ocr_text:

                comparison = "".join([comparison, ocr_word])
                fuzzy_ratios.append(fuzz.ratio(card.get('name'), comparison))
                max_ratio = max(fuzzy_ratios or [0])
                if (max_ratio > highest_ratio):
                    highest_ratio = max_ratio
                    highest_card.update({
                        'id': ocr_result[0],
                        'ratio': max_ratio,
                        'card': card,
                        'ocr': ocr_text
                    })
                if (highest_ratio == 100):
                    break

                if (highest_ratio < 85):
                    if (len(ocr_text) >= 2):
                        comparison = " ".join([ocr_text[1], ocr_text[0]])
                        fuzzy_ratios.append(fuzz.ratio(
                            card.get('name'), comparison))
                        max_ratio = max(fuzzy_ratios or [0])
                        if (max_ratio > highest_ratio):
                            highest_ratio = max_ratio
                            highest_card.update({
                                'id': ocr_result[0],
                                'ratio': max_ratio,
                                'card': card,
                                'ocr': ocr_text
                            })

        if highest_ratio >= 85:
            passed_cards.append(highest_card)
            print(
                f'Passed: {highest_ratio}, {ocr_result[1]}, {highest_card.get("card").get("foil")}, {ocr_result[3]}')  # type: ignore
        else:
            failed_cards.append(highest_card)
            print(f'Failed : {highest_ratio}, {highest_card}')
    return [passed_cards, failed_cards]


def match(card_db, ocr_db):
    card_set = [{'name': card.get('name'), 'price': card.get(
        'prices').get('usd') or card.get('prices').get('usd_foil'),
        'foil': card.get('foil')} for card in card_db]
    ocr_cursor = ocr_db.cursor()
    ocr_cursor.execute(
        'SELECT id, file_name, ocr_result, type FROM cards;')
    ocr_db_all = ocr_cursor.fetchall()

    chunk_size = 10  # Number of cards to process per chunk
    # ocr_result_chunks = [ocr_db_all[i:i+chunk_size] for i in range(0, 3)]
    ocr_result_chunks = [ocr_db_all[i:i+chunk_size]
                         #  for i in range(0, 1, 1)]  # type: ignore
                         for i in range(0, len(ocr_db_all), chunk_size)]  # type: ignore
    with concurrent.futures.ProcessPoolExecutor(max_workers=16) as executor:
        futures = []
        for chunk in ocr_result_chunks:
            # match_card(card_set, chunk)
            futures.append(executor.submit(match_card, card_set, chunk))
        for future in concurrent.futures.as_completed(futures):
            passed_cards, failed_cards = future.result()
            for passed_card in passed_cards:
                ocr_db.cursor().execute("INSERT INTO match_results (ocr_id,name,ocr_result,price,foil,ratio) VALUES (%s,%s,%s,%s,%s,%s)", (
                    passed_card.get('id'), passed_card.get('card').get(
                        'name'), passed_card.get('ocr'), passed_card.get('card').get('price'), passed_card.get('card').get('foil'), passed_card.get('ratio')
                ))
                ocr_db.commit()
            for failed_card in failed_cards:
                ocr_db.cursor().execute("INSERT INTO failed_results (ocr_id,name,ocr_result,price,foil,ratio) VALUES (%s,%s,%s,%s,%s,%s)", (
                    failed_card.get('id'), failed_card.get('card').get(
                        'name'), f'{failed_card.get("ocr")}', failed_card.get('card').get('price'), f'{failed_card.get("card").get("foil")}', failed_card.get('ratio')
                ))
                ocr_db.commit()


if __name__ == "__main__":
    main()
