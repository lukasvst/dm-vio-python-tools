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
import pyquaternion
import numpy as np
from numpy.linalg import inv
from ruamel.yaml import YAML


def line_to_transformation_matrix(line):
    # in the file there is timestamp,tx,ty,tz,w,x,y,z.
    translation = line[1:4]
    quat = pyquaternion.Quaternion(np.array(line[4:8]))
    transform_mat = np.eye(4, 4)
    transform_mat[0:3, 3] = np.array(translation).transpose()
    transform_mat[0:3, 0:3] = quat.rotation_matrix
    return transform_mat


def load_imu_to_cam(yaml_file):
    # We also need to convert from imuToWorld to camToWorld.
    yaml = YAML()
    with open(yaml_file, 'r') as camchain_file:
        camchain = yaml.load(camchain_file)
    return np.array(camchain['cam0']['T_cam_imu'])


def save_transform_to_line(changed_transform, line):
    line[1:4] = changed_transform[0:3, 3]
    quat = pyquaternion.Quaternion(matrix=changed_transform[0:3, 0:3])
    line[4:8] = quat.elements
    line[:] = map(str, line)


# Convert the groundtruth of TUM-VI to DSO Matlab format.
if __name__ == '__main__':
    dataset_folder = '/path/to/VIDataset'
    save_folder = '/path/to/save/groundtruth_tumvi'

    folders = ['dataset-corridor1_512_16',
               'dataset-corridor2_512_16',
               'dataset-corridor3_512_16',
               'dataset-corridor4_512_16',
               'dataset-corridor5_512_16',
               'dataset-magistrale1_512_16',
               'dataset-magistrale2_512_16',
               'dataset-magistrale3_512_16',
               'dataset-magistrale4_512_16',
               'dataset-magistrale5_512_16',
               'dataset-magistrale6_512_16',
               'dataset-outdoors1_512_16',
               'dataset-outdoors2_512_16',
               'dataset-outdoors3_512_16',
               'dataset-outdoors4_512_16',
               'dataset-outdoors5_512_16',
               'dataset-outdoors6_512_16',
               'dataset-outdoors7_512_16',
               'dataset-outdoors8_512_16',
               'dataset-room1_512_16',
               'dataset-room2_512_16',
               'dataset-room3_512_16',
               'dataset-room4_512_16',
               'dataset-room5_512_16',
               'dataset-room6_512_16',
               'dataset-slides1_512_16',
               'dataset-slides2_512_16',
               'dataset-slides3_512_16']

    for folder in folders:
        gt_file = Path(dataset_folder) / folder / 'dso' / 'gt_imu.csv'
        save_file = Path(save_folder) / 'gtFiles' / 'tumvi_{}.txt'.format(folder)
        with open(gt_file) as infile:
            inlines = infile.readlines()
        gt_split = [line.split(',') for line in inlines if not line.startswith('#')]
        for line in gt_split:
            line[0] = str(float(line[0]) * 1e-9)

        transform_cam_imu = load_imu_to_cam('tum_vi_configs/camchain.yaml')
        transform_imu_cam = inv(transform_cam_imu)
        for line in gt_split:
            transform_mat = line_to_transformation_matrix(line)  # this is T_w_imu
            # We want T_w_cam
            changed_transform = transform_mat @ transform_imu_cam
            # save changed transform.
            save_transform_to_line(changed_transform, line)
            line[-1] = line[-1] + '\n'

        gt_lines = [' '.join(line) for line in gt_split]
        with open(save_file, 'w') as savefile:
            savefile.writelines(gt_lines)

        # Save times files.
        times_file = Path(dataset_folder) / folder / 'dso' / 'cam0' / 'times.txt'
        times_target = Path(save_folder) / 'timesFiles' / 'tumvi_{}.txt'.format(folder)
        subprocess.run('cp {} {}'.format(times_file, times_target), shell=True)
