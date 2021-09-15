"""
Script for generating Aruco marker images.

Author: Nathan Sprague
Version: 10/26/2020
"""

import argparse
import cv2
import numpy as np


class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    """ Trick to allow both defaults and nice formatting in the help. """
    pass


def main():
    parser = argparse.ArgumentParser(formatter_class=CustomFormatter,
                                     description="Generates multiple .png images using a customized dictionary.")
    parser.add_argument('--size', default=200, type=int,
                        help='Side length in pixels')
    parser.add_argument('--num', default=100, type=int,
                        help='Amount of markers to be generated')
    parser.add_argument('--bits', default=6, type=int,
                        help='Amount of bits to use')
    parser.add_argument('--seed', default=0, type=int,
                        help='The seed used to generate the dictionary')

    args = parser.parse_args()

    dictionary = cv2.aruco.Dictionary_create(args.num, args.bits, args.seed)
    for i in range(args.num):
        image = np.zeros((args.size, args.size), dtype=np.uint8)
        image = cv2.aruco.drawMarker(dictionary, i, args.size, image, 1)
        cv2.imwrite("marker_{:04d}.png".format(i), image)


if __name__ == "__main__":
    main()
