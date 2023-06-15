import argparse
import csv
import glob
import os
import easyocr
import cv2
import tqdm
parser = argparse.ArgumentParser(description="Just a OCR reader for magic cards",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-i", "--image_dir", type=str, required=True)
parser.add_argument("-o", "--output_file", type=str,
                    required=False, default=None)
parser.add_argument("-b", "--batch_size", type=int, default=1)
parser.add_argument("-w", "--workers", type=int, default=0)
parser.add_argument("-d", "--details", type=int, default=1)
parser.add_argument("-bl", "--blocklist", type=str, default="")
parser.add_argument("-p", "--paragraph", type=bool, default=False)
parser.add_argument("-P", "--progress_only", type=bool, default=False)
parser.add_argument("-show", "--show-image", type=bool, default=True)
parser.add_argument("-fd", "--failed_dir", type=str, default=None)
parser.add_argument("-sd", "--success_dir", type=str, default=None)
parser.add_argument("-th", "--threshold", type=str, default=0.7)
args = parser.parse_args()


def main():

    # Retrieve all image paths that match the pattern
    files = glob.glob("*.jpg", root_dir=args.image_dir)

    reader = easyocr.Reader(['en'], gpu=True)
    writer = None
    output_file = None
    if (args.output_file is not None):
        print(f"Opening {args.output_file} for writing")
        output_file = open(args.output_file, "w")
        writer = csv.writer(output_file)
    with tqdm.tqdm(total=len(files)) as pbar:
        if (not args.progress_only):
            pbar.close()
        for file in files:
            file_path = os.path.join(args.image_dir, file)
            bounds = reader.readtext(file_path, batch_size=args.batch_size,
                                     workers=args.workers, detail=args.details, blocklist=args.blocklist, paragraph=args.paragraph, y_ths=0.2, x_ths=5, min_size=10)

            if (args.show_image):
                im = cv2.imread(file_path)
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
            if args.success_dir is not None:
                if (average_confidence(bounds) >= args.threshold):
                    if (args.progress_only is not True):
                        print("PASSED THRESHOLD: " + file)
                    if not os.path.exists(args.success_dir):
                        os.mkdir(args.success_dir)
                        cv2.imwrite(os.path.join(args.success_dir, file), im)

            if args.failed_dir is not None:
                if average_confidence(bounds) < args.threshold:
                    if args.output_file is not None:
                        bounds.append(average_confidence)
                        if not args.progress_only:
                            print("FAILED THRESHOLD: " + file)
                if not os.path.exists(args.failed_dir):
                    os.mkdir(args.failed_dir)

            if (args.output_file is not None):

                writer.writerow(bounds)
            if (args.progress_only):
                pbar.update()
            else:
                print(bounds)
                print("\n"*3)
                print('-'*100)
def average_confidence(bounds):
    sum_confidence = 0
    for bbox in bounds:
        confidence = bbox[len(bbox)-1]
        sum_confidence += confidence
    return sum_confidence / len(bounds)


if __name__ == '__main__':
    main()
