import glob
import itertools
import json
import os
import sys
import threading
import time
import cv2
import easyocr
import numpy as np
import yaml
import sqlite3
import ast
import concurrent.futures

from fuzzywuzzy import fuzz
config: dict = yaml.load(open('mysticocr.yml', 'r'),
                         Loader=yaml.FullLoader)['mystic']


def main():

    if (config.get('command') == "scan"):
        scan()
    elif (config.get('command') == "match"):
        match()


def scan():
    files = glob.glob(os.path.join(config['scan']['image_dir'], "*.jpg"))
    reader = easyocr.Reader(['en'], gpu=config['scan']['gpu'])
    db_connection = sqlite3.connect(config['scan']['output_db'])
    if config['overwrite_db'] is True:
        db_connection.execute('DROP TABLE IF EXISTS ocr_results;')
    db_connection.execute(
        'CREATE TABLE IF NOT EXISTS ocr_results (id INTEGER PRIMARY KEY AUTOINCREMENT, file_name TEXT,location TEXT,foil TEXT, showcase TEXT,ocr_result TEXT,image BLOB);')
    done = False
    count = 0

    def animated_loading(length: int):
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if done:
                break
            sys.stdout.write(
                f'\rScanning images: {c} {count}/{length} OR {round((count/length*100),3)}% completed')
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\rDone!            ')
    t = threading.Thread(target=animated_loading, args=[
                         len(files)], daemon=True)
    # t.start()
    for file in files:
        count += 1
        imagecv = cv2.imread(file)

        originalimagecv = imagecv.copy()
        if (config['scan']['card']['sideways'] is True):
            imagecv = cv2.rotate(imagecv, cv2.ROTATE_90_CLOCKWISE)

        result = reader.readtext(
            imagecv, width_ths=config['scan']['width_ths'], x_ths=config['scan']['x_ths'], batch_size=50)
        if config['scan']['show_image'] is True:
            for bbox in result:
                # Unpack the bounding box
                tl, tr, br, bl = bbox[0]
                tl = (int(tl[0]), int(tl[1]))
                tr = (int(tr[0]), int(tr[1]))
                br = (int(br[0]), int(br[1]))
                bl = (int(bl[0]), int(bl[1]))
                cv2.rectangle(imagecv, tl, br, (10, 255, 0),
                              10)
            cv2.imwrite(os.path.join(
                config['scan']['output_dir'], os.path.basename(file)), imagecv)
            cv2.imshow('Image', imagecv)
            cv2.waitKey(1)  # 1 to make sure image updates
        db_connection.execute(
            "INSERT INTO ocr_results (file_name,location,foil,showcase,ocr_result,image) VALUES (?,?,?,?,?,?);",
            (file, config['scan']['card']['location'],
             config['scan']['card']['foil'], config['scan']['card']['showcase'], f'{result}', sqlite3.Binary(cv2.imencode(".jpg", originalimagecv)[1].tobytes())))
        db_connection.commit()
    done = True


def match_card(card_set, chunk):  # type: ignore
    count = 0
    length = len(chunk)
    highest_cards = []
    results = []
    highest_ratios = []
    for ocr_result in chunk:
        count += 1
        highest_ratio = 0
        highest_card = dict()
        ocr_1st_element = ast.literal_eval(ocr_result[5])[0][1]
        ocr_2nd_element = ast.literal_eval(ocr_result[5])[1][1]
        ocr_3rd_element = ast.literal_eval(ocr_result[5])[2][1]
        for name in card_set:
            name = name.split("//")[0]
            fuzz_ratio_1 = fuzz.ratio(ocr_1st_element, name)
            fuzz_ratio_2 = fuzz.ratio(ocr_2nd_element, name)
            fuzz_ratio_3 = fuzz.ratio(
                " ".join([ocr_1st_element, ocr_2nd_element]), name)
            fuzz_ratio_4 = fuzz.ratio(
                " ".join([ocr_1st_element, ocr_2nd_element, ocr_3rd_element]), name)
            fuzz_ratio = max([fuzz_ratio_1, fuzz_ratio_2,
                             fuzz_ratio_3, fuzz_ratio_4])
            if fuzz_ratio > highest_ratio:
                highest_ratio = fuzz_ratio
                highest_card = name
        print(
            f'highest_ratio: {highest_ratio} :{highest_card} : {count}/{length} : {ocr_result[1]} : CON: {ocr_result[2]}')
        highest_cards.append(highest_card)
        results.append(ocr_result)
        highest_ratios.append(highest_ratio)
    return [highest_cards, results, highest_ratios]


def match():
    card_db: list = json.loads(
        open(config['match']['card_db'], 'r', encoding='utf-8').read())
    card_set = {card.get('name') for card in card_db}
    db_connection = sqlite3.connect(config['match']['db'])
    db_cursor = db_connection.cursor()
    db_cursor.execute(
        'SELECT * FROM ocr_results;')
    ocr_results = db_cursor.fetchall()

    if (config['overwrite_db'] is True):
        db_connection.execute("DROP TABLE IF EXISTS match_results;")
    db_connection.execute(
        "CREATE TABLE IF NOT EXISTS match_results (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,file_name TEXT,foil TEXT, showcase TEXT,location TEXT, ocr_result TEXT,ratio INT,image BLOB);")
    chunk_size = 50  # Number of cards to process per chunk
    ocr_result_chunks = [ocr_results[i:i+chunk_size]
                         for i in range(0, len(ocr_results), chunk_size)]  # type: ignore
    with concurrent.futures.ProcessPoolExecutor(max_workers=14) as executor:
        futures = []
        for chunk in ocr_result_chunks:
            futures.append(executor.submit(match_card, card_set, chunk))
        for future in concurrent.futures.as_completed(futures):
            highest_cards, ocr_results, highest_ratios = future.result()
            # type: ignore
            for highest_card, ocr_result, highest_ratio in zip(highest_cards, ocr_results, highest_ratios):
                db_connection.execute("INSERT INTO match_results (name,file_name,location,foil,showcase,ocr_result,ratio,image) VALUES (?,?,?,?,?,?,?,?);", (
                    highest_card, ocr_result[1], ocr_result[2], ocr_result[3], ocr_result[4], ocr_result[5], highest_ratio, ocr_result[6]))
                db_connection.commit()


def calc_avg_confidence(result):
    if len(result) == 0:
        return -1
    sum_confidence = 0
    for bbox in result:
        confidence = bbox[-1]
        sum_confidence += confidence
    return sum_confidence / len(result)


if __name__ == '__main__':
    main()
