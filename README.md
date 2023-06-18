# OCR Magic Card Reader

This is a Python script that uses EasyOCR to perform optical character recognition (OCR) on images of Magic cards. It extracts text from the images and optionally saves the results to a CSV file. It also provides options for displaying the annotated images and monitoring progress.
# Steps
This script requires 3 steps to function properly.

  1. Scan the image into a results.csv file
  2. Convert the cards json file to a sqlite database
  3. Finally, match the results.csv file to each card in the sqlite database
## Usage (Scanning the images)
```
python ./MysticOCR.py -i ./data/ -sd ./successful -fd ./failed/ -o results.csv
```
#### Explaination
``-i / --image_dir`` (required) is the directory where the card images would be read from.

``-sd / --success_dir`` (Not required) is the result of the card images which passed the threshold.

``-fd / --failed_dir`` (Not required) is the result of the card images which did NOT pass the threshold. (Usually sideways image card, double cards on one face)

``-o / --output_file`` (require) is where the text of the image and bounding boxes of that text will be stored (to be used with MatchScryfall.py)


## Usage (Converting 'default cards' json file to sqlite)
```
python ./ConvertScryfallToSqlite.py -i input_file.json -o output_file.json
```
#### Explaination

``-i / --input_file`` is the path to the downloaded Scryfall (default cards) json file

``-o / --output_file`` is the path to where you want the database to be saved and used with MatchScryfall.py


## Usage (Matching the result.csv to Scryfall Sqlite database)
```
python ./MatchScryfall.py -c results.csv -db scryfall_cards.db
```
#### Explaination
``-c / --csv_file`` is the path to the output_file from ./MysticOCR.py

``-db / --database_file`` is the path to the Scryfall database

``-o / --output_file`` (NEEDS TO BE ADDED)

# TODO
- Add MatchScryfall's output_file functionality.
- Add set recognition & detection, (If anyone could help with this that'd be great) Just create a pull request!

