import cv2
import easyocr


class MysticOCR:
    reader: easyocr.Reader
    config: dict

    def __init__(self, config):
        self.config = config
        self.reader = easyocr.Reader(["en"])
        return None

    def scan_file(self, file_path):
        originaL_imagecv = cv2.imread(file_path)
        image = originaL_imagecv.copy()
        if self.config["scan"]["card"]["sideways"]:
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        ocr_result = self.reader.readtext(
            image,
            width_ths=self.config["scan"]["width_ths"],
            x_ths=self.config["scan"]["x_ths"],
            batch_size=100,
        )
        return [ocr_result, originaL_imagecv]

    def show_image(self, image, ocr_result):
        for bbox in ocr_result:
            # Unpack the bounding box
            tl, tr, br, bl = bbox[0]
            tl = (int(tl[0]), int(tl[1]))
            tr = (int(tr[0]), int(tr[1]))
            br = (int(br[0]), int(br[1]))
            bl = (int(bl[0]), int(bl[1]))
            cv2.rectangle(image, tl, br, (10, 255, 0), 10)  # type: ignore
        cv2.imshow("Image", image)
        cv2.waitKey(1)
