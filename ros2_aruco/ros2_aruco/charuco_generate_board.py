"""
Script for generating a ChArUco marker board.

Author: Floris Erich
Version: 2021/11/18
"""

import argparse
import cv2
import os
from cv2 import aruco


def main():
    parser = argparse.ArgumentParser(
        description='Generate a ChArUco marker board.')
    parser.add_argument('--square-x',
                        default=7,
                        type=int,
                        help='Number of chessboard squares in X direction')
    parser.add_argument('--square-y',
                        default=5,
                        type=int,
                        help='Number of chessboard squares in Y direction')
    parser.add_argument('--square-length',
                        default=0.1,
                        type=float,
                        help='Chessboard square side length (normally in meters)')  # noqa
    parser.add_argument('--marker-length',
                        default=0.08,
                        type=float,
                        help='Marker side length (same unit as square length)')
    parser.add_argument('--path',
                        type=str,
                        default='./checkerboard.tiff',
                        help='Path to write the checkerboard to')
    parser.add_argument('--out-x',
                        type=int,
                        help='Number of pixels for output, in X direction. If not specified, 300 * SQUARE_X')  # noqa
    parser.add_argument('--out-y',
                        type=int,
                        help='Number of pixels for output, in Y direction. If not specified, 300 * SQUARE_Y')  # noqa
    dict_options = [s for s in dir(cv2.aruco) if s.startswith("DICT")]
    option_str = ", ".join(dict_options)
    dict_help = f"Dictionary to use. Valid options include: {option_str}"
    parser.add_argument('--dictionary',
                        default='DICT_5X5_250',
                        type=str,
                        choices=dict_options,
                        help=dict_help, metavar='')
    args = parser.parse_args()
    args.out_x = args.out_x or 300 * args.square_x
    args.out_y = args.out_y or 300 * args.square_y

    try:
        dictionary_id = cv2.aruco.__getattribute__(args.dictionary)
        dictionary = cv2.aruco.Dictionary_get(dictionary_id)
    except AttributeError:
        print(f'unrecognized dictionary id: {args.dictionary}')
        print('Valid options:')
        for s in [s for s in dir(cv2.aruco) if s.startswith('DICT')]:
            print(s)
        return

    board = aruco.CharucoBoard_create(args.square_x,
                                      args.square_y,
                                      args.square_length,
                                      args.marker_length,
                                      dictionary)
    imboard = board.draw((args.out_x, args.out_y))
    written = cv2.imwrite(args.path, imboard)

    abs_path = os.path.abspath(args.path)
    if not written:
        print(f'Failed to write checkerboard to {abs_path}')
    else:
        print(f'Succesfully wrote checkerboard to {abs_path}')


if __name__ == '__main__':
    main()
