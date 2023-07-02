import glob
import json
import os
import yaml
from classes.Matcher import Matcher
from classes.Database import Database
from classes.OCR import MysticOCR


def main():
    print("Loading configuration...")
    config = yaml.load(open("mysticocr.yml", "r"), Loader=yaml.FullLoader)["mystic"]
    print("Loading images...")
    files = glob.glob(
        os.path.join(config["scan"]["image_dir"], "**/*.jpg"), recursive=True
    )
    print("Loading Database...")
    db: Database = Database(config)

    if config.get("command") == "scan":
        print("Loading OCR...")
        ocr: MysticOCR = MysticOCR(config)
        for file in files:
            print(f"Scanning file: " + file)
            ocr_result, imagecv = ocr.scan_file(file)
            if config["scan"]["show_image"]:
                ocr.show_image(imagecv, ocr_result)
            db.insert_ocr_result(file, ocr_result, imagecv)
    elif config.get("command") == "match":
        card_set = json.loads(open("db_6-29-2023.json", "r", encoding="utf-8").read())
        # db.import_card_set(card_set)
        matcher: Matcher = Matcher(config, card_set, db)
        matcher.chunkify(1)
        matcher.search_with_local_db()
        # matcher.create_workers()


if __name__ == "__main__":
    main()
