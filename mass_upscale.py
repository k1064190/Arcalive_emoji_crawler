import pathlib
import os
import pyanime4k
from pyanime4k import ac
import cv2 as cv
import PIL
from PIL import Image
import numpy as np

# ac.AC.list_GPUs()

image_dir = pathlib.Path('./test')
output_dir = pathlib.Path('./output')

def main():
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    parameters1 = ac.Parameters()
    # enable HDN for ACNet
    parameters1.HDN = True
    parameters1.zoomFactor = 5.12

    parameters2 = ac.Parameters()
    parameters2.HDN = True
    parameters2.zoomFactor = 2.56

    a1 = ac.AC(
        managerList=ac.ManagerList([ac.OpenCLACNetManager(pID=0, dID=0)]),
        type=ac.ProcessorType.OpenCL_ACNet,
        parameters=parameters1
    )

    a2 = ac.AC(
        managerList=ac.ManagerList([ac.OpenCLACNetManager(pID=0, dID=0)]),
        type=ac.ProcessorType.OpenCL_ACNet,
        parameters=parameters2
    )

    # list all images in the directory
    images_path = list(image_dir.glob('*.png'))

    for image_path in images_path:
        image = cv.imread(str(image_path))
        if image.shape[0] == 100:
            a1.load_image_from_numpy(image, input_type=ac.AC_INPUT_RGB)
            a1.process()
            a1.save_image(str(output_dir / image_path.name))
        else:
            a2.load_image_from_numpy(image, input_type=ac.AC_INPUT_RGB)
            a2.process()
            a2.save_image(str(output_dir / image_path.name))


if __name__ == '__main__':
    main()