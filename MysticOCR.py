import argparse
import csv
import glob
import os
import easyocr
import cv2
import tqdm
parser = argparse.ArgumentParser(description="Just a OCR reader for magic cards",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-i", "--image_path", type=str, required=True)
parser.add_argument("-o", "--output", type=str, required=False)
parser.add_argument("-b", "--batch_size", type=int, default=500)
parser.add_argument("-w", "--workers", type=int, default=0)
parser.add_argument("-d", "--details", type=int, default=2)
parser.add_argument("-bl", "--blocklist", type=str, default="")
parser.add_argument("-p", "--paragraph", type=bool, default=True)
parser.add_argument("-P", "--progress_only", type=bool, default=False)
parser.add_argument("-show", "--show-image", type=bool, default=True)
args = parser.parse_args()


def main():

    # Retrieve all image paths that match the pattern
    files = glob.glob("*.jpg", root_dir=args.image_path)

    reader = easyocr.Reader(['en'], gpu=True)
    writer = None
    output_file = None
    if (args.output is not None):
        print(f"Opening {args.output} for writing")
        output_file = open(args.output, "w")
        writer = csv.writer(output_file)
    with tqdm.tqdm(total=len(files)) if (args.progress_only) else None as pbar:
        if (not args.progress_only):
            pbar.close()

        for file in files:
            file = os.path.join(args.image_path, file)
            bounds = reader.readtext(file, batch_size=args.batch_size,
                                     workers=args.workers, detail=args.details, blocklist=args.blocklist, paragraph=True, y_ths=0.2, x_ths=10, min_size=10)

            if (args.show_image):
                im = cv2.imread(file)
                for (bbox) in bounds:
                    # unpack the bounding box
                    (tl, tr, br, bl) = bbox[0]
                    tl = (int(tl[0]), int(tl[1]))
                    tr = (int(tr[0]), int(tr[1]))
                    br = (int(br[0]), int(br[1]))
                    bl = (int(bl[0]), int(bl[1]))
                    cv2.rectangle(im, tl, br, (10, 255, 0), 2)
                cv2.imshow('Image', im)
                cv2.waitKey(1)
            if (args.progress_only):
                pbar.update()
            else:
                print(bounds)
                print("\n"*3)
                print('-'*100)
            if (args.output is not None):
                writer.writerow(bounds)


if __name__ == '__main__':
    main()
