import numpy as np
import cv2 as cv
from imagededup.methods import PHash
import os
import shutil

image_dir = './store_200'
dupe_dir = './dupes'


def main():
    phasher = PHash()

    encodings = phasher.encode_images(image_dir=image_dir)

    duplicates = phasher.find_duplicates(encoding_map=encodings, max_distance_threshold=10)

    print(duplicates)

    # plot_duplicates(image_dir='path/to/image/directory',
    #                 duplicate_map=duplicates,
    #                 filename='ukbench00120.jpg')
    # example output:
    # {'01_00000000.png': [], '01_00000001.png': [], '01_00000002.png': [],
    # '01_00000003.png': ['01_00000004.png'], '01_00000004.png': ['01_00000003.png'],
    # '01_00000005.png': [], '01_00000006.png': [], '01_00000007.png': ['01_00000008.png'], ...

    # move duplicates to dupe_dir
    for i, (k, v) in enumerate(duplicates.items()):
        if len(v) > 0:
            for dupe in v:
                # image_idx integer
                image_idx = int(dupe.split('.')[0].split('_')[1])
                # continue if image_idx < i
                if image_idx < i:
                    continue
                # if image exists
                if os.path.exists(os.path.join(image_dir, dupe)):
                    # move image to dupe_dir
                    shutil.move(os.path.join(image_dir, dupe), os.path.join(dupe_dir, dupe))


if __name__ == '__main__':
    main()
