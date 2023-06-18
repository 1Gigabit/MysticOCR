import argparse
import csv
import glob
import itertools
import os
import sys
from threading import Thread
import threading
import time
import easyocr
import cv2
import tqdm

# Define the command-line arguments
parser = argparse.ArgumentParser(description="Just an OCR reader for magic cards",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-i", "--image_dir", type=str, required=True)
parser.add_argument("-o", "--output_file", type=str, default=None)
parser.add_argument("-b", "--batch_size", type=int, default=1)
parser.add_argument("-w", "--workers", type=int, default=0)
parser.add_argument("-d", "--details", type=int, default=1)
parser.add_argument("-bl", "--blocklist", type=str, default="")
parser.add_argument("-p", "--paragraph", default=False)
parser.add_argument("-P", "--progress", default=False)
parser.add_argument("-show", "--show_image", default=True)
parser.add_argument("-fd", "--failed_dir", type=str, default=None)
parser.add_argument("-sd", "--success_dir", type=str, default=None)
parser.add_argument("-th", "--threshold", type=float, default=0.6)
parser.add_argument("-wth", "--width_ths", type=float, default=3)
parser.add_argument("-xth", "--x_ths", type=float, default=4)
parser.add_argument("-q", "--quiet", default=False)
args = parser.parse_args()


def log(message):
    if args.quiet is False:
        print(f'[{time.process_time()}] : {message}')


def main():
    log(f'Opening image_dir...')
    files = glob.glob(os.path.join(args.image_dir, "*.jpg"))
    log(f'Creating EasyOCR reader...')
    reader = easyocr.Reader(['en'], gpu=True)
    writer = None
    pbar = None # Todo
    log_file = None # Todo
    done = False
    file = None
    count = 0
    if args.output_file is not None:
        log(f"Opening output CSV file for writing...")
        output_file = open(args.output_file, "w")
        writer = csv.writer(output_file)
    if args.progress is True:
        log(f'Creating progress bar...')
        pbar = tqdm.tqdm(total=len(files)) # Todo

    def animated_loading():
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if done:
                break
            sys.stdout.write(f'\rScanning images: {c} {count}/{len(files)} OR {round((count/len(files)*100),3)}% completed')
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\rDone!             ')
    t = threading.Thread(target=animated_loading, daemon=True)
    t.start()
    for file in files:
        count += 1
        bounds = reader.readtext(file, batch_size=args.batch_size,
                                 workers=args.workers, detail=args.details, blocklist=args.blocklist,
                                 paragraph=args.paragraph, x_ths=args.x_ths, width_ths=args.width_ths, min_size=10)
        if args.show_image:
            im = cv2.imread(file)
            for bbox in bounds:
                # Unpack the bounding box
                tl, tr, br, bl = bbox[0]
                tl = (int(tl[0]), int(tl[1]))
                tr = (int(tr[0]), int(tr[1]))
                br = (int(br[0]), int(br[1]))
                bl = (int(bl[0]), int(bl[1]))
                cv2.rectangle(im, tl, br, (10, 255, 0), 2)
            im = cv2.resize(im, (480, 600))
            cv2.imshow('Image', im)

            cv2.waitKey(1)  # 1 to make sure image updates

        avg_confidence = calc_avg_confidence(bounds)
        bounds.append(avg_confidence)
        if avg_confidence >= args.threshold:
            if args.success_dir is not None:
                os.makedirs(args.success_dir, exist_ok=True)
                success_file = os.path.join(
                    args.success_dir, f"{avg_confidence}__"+os.path.basename(file))
                cv2.imwrite(success_file, im)
        else:
            if args.failed_dir is not None:
                os.makedirs(args.failed_dir, exist_ok=True)
                failed_file = os.path.join(
                    args.failed_dir, f"{avg_confidence}__"+os.path.basename(file))
                cv2.imwrite(failed_file, im)
        if writer is not None:
            writer.writerow(bounds)
    done = True


def calc_avg_confidence(bounds):
    if len(bounds) == 0:
        return -1
    sum_confidence = 0
    for bbox in bounds:
        confidence = bbox[-1]
        sum_confidence += confidence
    return sum_confidence / len(bounds)


if __name__ == '__main__':
    main()
