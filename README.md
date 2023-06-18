# OCR Magic Card Reader

This is a Python script that uses EasyOCR to perform optical character recognition (OCR) on images of Magic cards. It extracts text from the images and optionally saves the results to a CSV file. It also provides options for displaying the annotated images and monitoring progress.

## Requirements

- Python 3.7 or higher
- OpenCV (cv2) library
- EasyOCR library
- tqdm library

## Installation

1. Clone the repository or download the script.
2. Install the required dependencies by running the following command:
   ```shell
   pip install opencv-python easyocr tqdm
   ```

## Usage

The script can be executed with the following command:

```shell
python MysticOCR.py.py -i <image_path> [-o <output_file>] [-b <batch_size>] [-w <workers>] [-d <details>] [-bl <blocklist>] [-p <paragraph>] [-P <progress_only>] [-show <show_image>]
```

### Arguments (Needs to be updated)

- `-i, --image_path` (required): The path to the directory containing the input images. Images should be in JPEG format.
- `-o, --output_file` (optional): The path to the output CSV file to save the OCR results. If not specified, the results will not be saved.
- `-b, --batch_size` (optional): The batch size for processing images. Default is 500.
- `-w, --workers` (optional): The number of worker processes to use for parallel processing. Default is 0 (no additional workers).
- `-d, --details` (optional): The level of detail for the OCR results. Set to 0 for only text, 1 for text with bounding boxes, or 2 for text with detailed information. Default is 2.
- `-bl, --blocklist` (optional): A string of characters to be ignored during OCR. Default is an empty string.
- `-p, --paragraph` (optional): Boolean flag to enable paragraph mode for OCR. If enabled, the script will attempt to group text into paragraphs. Default is True.
- `-P, --progress_only` (optional): Boolean flag to enable progress-only mode. If enabled, only the progress bar will be displayed, and OCR results will not be printed or saved. Default is False.
- `-show, --show-image` (optional): Boolean flag to enable image display with bounding box annotations. Default is True.
- `-fd, --failed_dir` (optional): The directory to save images that failed to meet the confidence threshold.
- `-sd, --success_dir` (optional): The directory to save images that passed the confidence threshold.
- `-th, --threshold` (optional, default: 0.7): The confidence threshold for determining if the OCR result is successful.

### Example

```shell
python MysticOCR.py.py -i input_images/ -o results.csv -b 200 -w 4 -d 1 -bl "0123456789" -p True -P False -show True
```
This example command runs the OCR magic card reader script on images in the "input_images" directory. It saves the results to "results.csv" in CSV format. The batch size is set to 200, and 4 worker processes are used for parallel processing. The OCR results include text with bounding box annotations. The characters "0123456789" are ignored during OCR. Paragraph mode is enabled, and the script will display the image with bounding box annotations. Progress updates will be printed during processing.

# Matching to Scryfall database

Get the latest database ("Default cards") from Scryfall!
https://scryfall.com/docs/api/bulk-data

```shell
python MatchScryfall -c results.csv -db db.json 
```
### TODO

- Rewrite arguments section of README.

Add set recognition & detection, (If anyone could help with this that'd be great.)

Just create a pull request!

