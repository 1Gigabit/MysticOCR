import argparse
import glob
import itertools
import json
import os
import sys
import threading
import time
import cv2
import easyocr
import yaml
import sqlite3
config: dict = yaml.load(open('mysticocr.yml', 'r'),
                         Loader=yaml.FullLoader)['mystic']


def main():

    if (config.get('command') == "scan"):
        scan()


def scan():
    files = glob.glob(os.path.join(config['scan']['image_dir'], "*.jpg"))
    reader = easyocr.Reader(['en'], gpu=config['scan']['gpu'])
    count = 0
    db_connection = sqlite3.connect(config['scan']['output_db'])
    db_cursor = db_connection.cursor()
    done = False
    db_cursor.execute(
        'CREATE TABLE IF NOT EXISTS ocr_results (id INTEGER PRIMARY KEY AUTOINCREMENT, file_name TEXT,card_type TEXT,foil TEXT,set TEXT,rarity TEXT,ocr_result TEXT);')

    def animated_loading():
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if done:
                break
            sys.stdout.write(
                f'\rScanning images: {c} {count}/{len(files)} OR {round((count/len(files)*100),3)}% completed')
            sys.stdout.flush()
            time.sleep(0.1)

    sys.stdout.write('\rDone!            ')
    t = threading.Thread(target=animated_loading, daemon=True)
    t.start()
    for file in files:
        count += 1
        result = reader.readtext(
            file, width_ths=config['scan']['width_ths'], x_ths=config['scan']['x_ths'])
        imagecv = cv2.imread(file)
        if config['scan']['show_image'] is True:
            for bbox in result:
                # Unpack the bounding box
                tl, tr, br, bl = bbox[0]  # type: ignore
                tl = (int(tl[0]), int(tl[1]))
                tr = (int(tr[0]), int(tr[1]))
                br = (int(br[0]), int(br[1]))
                bl = (int(bl[0]), int(bl[1]))
                cv2.rectangle(imagecv.copy(),
                              (tl[0], tl[1], br[1], br[0]), (10, 255, 0), 2)

            imagecv = cv2.resize(imagecv, (480, 600))
            cv2.imshow('Image', imagecv)
            cv2.waitKey(1)  # 1 to make sure image updates
        if (config['scan']['success_dir'] != ""):
            os.makedirs(config['scan']['success_dir'], exist_ok=True)
            cv2.imwrite(os.path.join(
                config['scan']['success_dir'], os.path.basename(file)), imagecv)
        if (config['scan']['fail_dir'] != ""):
            os.makedirs(config['scan']['fail_dir'], exist_ok=True)
            cv2.imwrite(os.path.join(
                config['scan']['fail_dir'], os.path.basename(file)), imagecv)

        db_connection.execute(
            "INSERT INTO ocr_results (file_name,card_type,foil,set,rarity,ocr_result) VALUES (?,?,?,?,?,?);",
            (file, config['scan']['card']['type'],
             config['scan']['card']['foil'],
             config['scan']['card']['set'],
             config['scan']['card']['rarity'], f'{result}'))
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
