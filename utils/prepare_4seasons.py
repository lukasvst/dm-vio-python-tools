# BSD 3-Clause License
#
# This file is part of the DM-VIO-Python-Tools.
# https://github.com/lukasvst/dm-vio-python-tools
#
# Copyright (c) 2022, Lukas von Stumberg, TUM
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
# disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
# following disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import subprocess

from utils.convert_groundtruth_4seasons import convert_groundtruth
from interpolate_imu_file import interpolate_imu_file
from pathlib import Path
from tqdm import tqdm


def filter_times_file(times_in, times_out, image_folder):
    """Filter lines of times file which don't have a corresponding file in the image folder."""
    with open(times_in) as infile:
        in_lines = infile.readlines()
    lines_split = [line.split(' ') for line in in_lines if not line.startswith('#')]
    images = {file.name.split('.')[0] for file in image_folder.iterdir() if file.is_file()}
    filtered_lines = [line for line in lines_split if line[0] in images]
    assert (len(filtered_lines) == len(images))
    outlines = [' '.join(line) for line in filtered_lines]
    with open(times_out, 'w') as outfile:
        outfile.writelines(outlines)


def crop_images(image_folder, target_folder):
    """ Crop all images, removing the bottom pixels (because it shows the car hood).
        We crop to image height 304 (only removing pixels at the top).
        For running DM-VIO with the config 4seasons this is not necessary, as the camerra calibration file defines
        a runtime cropping which is equivalent ot this.
    """
    if not (target_folder.exists()):
        target_folder.mkdir(parents=True)
    # 'convert test.png -crop 800x312+0+0 cropped.png'
    image_files = [file for file in image_folder.iterdir() if file.suffix == '.png']
    for file in tqdm(image_files):
        targ_name = target_folder / file.name
        command = 'convert {} -crop 800x304+0+0 {}'.format(file, targ_name)
        subprocess.run(command, shell=True)


def prepare4seasons(dataset_folder, groundtruth_save_folder, folders, general_preparation: bool,
                    create_cropped_images: bool):
    if general_preparation:
        print("Preparing times files and IMU data")
        for folder in tqdm(folders):
            if not (Path(dataset_folder) / folder).exists():
                print("WARNING: folder {} does not exist. --> Skipping.".format(folder))
                continue
            # copy times file to undistorted_images folder
            times_file = Path(dataset_folder) / folder / 'times.txt'
            times_target = Path(dataset_folder) / folder / 'undistorted_images'
            # For some of the sequences there are more lines in the times file than images in the folder,
            # so we filter them first.
            filter_times_file(times_file, times_target / 'times.txt', times_target / 'cam0')

            imu_in = Path(dataset_folder) / folder / 'imu.txt'
            imu_out = Path(dataset_folder) / folder / 'imu_interp.txt'
            interpolate_imu_file(imu_in, times_file, imu_out)

        print("Converting groundtruths")
        convert_groundtruth(dataset_folder, groundtruth_save_folder, folders)

    if create_cropped_images:
        print('Cropping images')
        for folder in tqdm(folders):
            if not (Path(dataset_folder) / folder).exists():
                print("WARNING: folder {} does not exist. --> Skipping.".format(folder))
                continue
            crop_images(Path(dataset_folder) / folder / 'undistorted_images' / 'cam0',
                        Path(dataset_folder) / folder / 'cropped_images' / 'cam0')
            # crop_images(Path(dataset_folder) / folder / 'undistorted_images' / 'cam1', Path(dataset_folder) /
            # folder / 'cropped_images' / 'cam1') # Uncomment if you intent to also run stereo methods.
            # Also copy times to cropped folder!
            subprocess.run('cp {} {}'.format(Path(dataset_folder) / folder / 'undistorted_images' / 'times.txt',
                                             Path(dataset_folder) / folder / 'cropped_images' / 'times.txt'),
                           shell=True)
