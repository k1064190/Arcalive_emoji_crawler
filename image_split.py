import cv2 as cv
import pathlib
import PIL
from PIL import Image
import os
import shutil

image_dir = pathlib.Path('./store')

def main():
    images_path = list(image_dir.glob('*.png'))

    store_100 = './store_100'
    store_200 = './store_200'

    if not os.path.exists(store_100):
        os.mkdir(store_100)
    if not os.path.exists(store_200):
        os.mkdir(store_200)

    for image_path in images_path:
        try:
            image_metadata = Image.open(str(image_path))
        except PIL.UnidentifiedImageError:
            print(f"cannot open {image_path}")
            os.remove(str(image_path))
            continue
        # get image size
        width, height = image_metadata.size

        image_metadata.close()

        if width == 100:
            # move to store_100 folder
            shutil.move(str(image_path), os.path.join(store_100, image_path.name))
        elif width == 200:
            # move to store_200 folder
            shutil.move(str(image_path), os.path.join(store_200, image_path.name))

if __name__ == '__main__':
    main()
