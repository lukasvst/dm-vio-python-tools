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

from pathlib import Path
import subprocess
from tqdm import tqdm

from utils.convert_groundtruth_tumvi import line_to_transformation_matrix, load_imu_to_cam, save_transform_to_line


def convert_groundtruth(dataset_folder, save_folder, folders):
    for folder in tqdm(folders):
        if not (Path(dataset_folder) / folder).exists():
            print("WARNING: folder {} does not exist. --> Skipping.".format(folder))
            continue
        gt_file = Path(dataset_folder) / folder / 'GNSSPoses.txt'
        save_file = Path(save_folder) / 'gtFiles' / '4seasons_{}.txt'.format(folder)
        if not (Path(save_folder) / 'gtFiles').exists():
            (Path(save_folder) / 'gtFiles').mkdir()
        if not (Path(save_folder) / 'timesFiles').exists():
            (Path(save_folder) / 'timesFiles').mkdir()

        with open(gt_file) as infile:
            inlines = infile.readlines()
        gt_split = [line.split(',') for line in inlines if not line.startswith('#')]

        orig_times = [line[0] for line in gt_split]

        # 4Seasons GT files save camToWorld already so we only need to convert the timestamp for the Matlab GT.
        for line in gt_split:
            line[0] = str(float(line[0]) * 1e-9)
            # We need to multiply the translation vector with the scale
            scale = float(line[8])
            line[1:4] = [str(float(x) * scale) for x in line[1:4]]
            # We only want the first 8 elements though.
            line[:] = line[0:8]
            # And we want to w,x,y,z (instead of x,y,z,w)
            line.insert(4, line.pop(7))
            line[-1] = line[-1] + '\n'

        gt_lines = [' '.join(line) for line in gt_split]
        with open(save_file, 'w') as savefile:
            savefile.writelines(gt_lines)

        # Also save groundtruth for visualization (which wants poses in imu to to world.
        save_viz_file = Path(dataset_folder) / folder / "GNSSPoses_IMU.txt"
        camchain_file = Path(dataset_folder) / 'calibration' / 'camchain.yaml'
        transform_cam_imu = load_imu_to_cam(camchain_file)
        for i, line in enumerate(gt_split):
            transform_mat = line_to_transformation_matrix(line)  # this is T_w_cam
            # We want T_w_imu
            changed_transform = transform_mat @ transform_cam_imu
            # save changed transform.
            save_transform_to_line(changed_transform, line)
            line[-1] = line[-1] + '\n'
            # This file should have original long timestamps
            line[0] = orig_times[i]

        gt_lines = [','.join(line) for line in gt_split]
        with open(save_viz_file, 'w') as savefile:
            savefile.writelines(gt_lines)

        # Save times files.
        # use the trimmed times file in undistorted_images, not the original one in the main folder!
        times_file = Path(dataset_folder) / folder / 'undistorted_images' / 'times.txt'
        times_target = Path(save_folder) / 'timesFiles' / '4seasons_{}.txt'.format(folder)
        subprocess.run('cp {} {}'.format(times_file, times_target), shell=True)
