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
import argparse
from pathlib import Path
from ruamel.yaml import YAML

from utils.config_utils import read_config, replace_dataset_in_config, shall_replace_dataset_in_config


def main():
    parser = argparse.ArgumentParser(
        description='Download all (or just one) sequences of the EuRoC dataset and write the path to them to the '
                    'config file.')

    parser.add_argument('--folder', type=str, help='Location where the dataset shall be downloaded to.', required=True)
    parser.add_argument('--only_seq', default=None, type=int,
                        help='Only download one sequence (with the given index starting with 0).')
    args = parser.parse_args()

    yaml = YAML()
    config, config_name, general_config, all_configs = read_config(None, yaml)
    if config is None:
        print('Error: There is no default config for this machine yet. Have you called create_config.py yet?')
        return

    print(
        "Please check the website of the EuRoC dataset for license information: "
        "https://projects.asl.ethz.ch/datasets/doku.php?id=kmavvisualinertialdatasets\n"
        "This download script was not created or is otherwise affiliated with the creators of the dataset, "
        "hence the links could change and it might stop working.")

    target_folder = Path(args.folder)

    will_replace_dataset_in_config = shall_replace_dataset_in_config(config, 'euroc', target_folder)

    if not target_folder.exists():
        target_folder.mkdir()

    folders = ['MH_01_easy', 'MH_02_easy', 'MH_03_medium', 'MH_04_difficult', 'MH_05_difficult',
               'V1_01_easy', 'V1_02_medium', 'V1_03_difficult', 'V2_01_easy', 'V2_02_medium', 'V2_03_difficult']
    prefixes = ['machine_hall', 'machine_hall', 'machine_hall', 'machine_hall', 'machine_hall',
                'vicon_room1', 'vicon_room1', 'vicon_room1', 'vicon_room2', 'vicon_room2', 'vicon_room2']

    only_seq = args.only_seq
    if not only_seq is None:
        folders = [folders[only_seq]]  # only download this sequence
        prefixes = [prefixes[only_seq]]

    # Insert into config
    if will_replace_dataset_in_config:
        replace_dataset_in_config(config, 'euroc', target_folder)
        print("Saving updated config.")
        with open('configs.yaml', 'w') as config_file:
            yaml.dump(all_configs, config_file)

    # -------------------- Download! --------------------
    general_command = 'wget http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset'
    for i, folder in enumerate(folders):
        if (target_folder / folder).exists():
            print('Folder exists --> skipping sequence {}'.format(folder))
            continue
        command = '{}/{}/{}/{}.zip'.format(general_command, prefixes[i], folder, folder)
        subprocess.run(command, cwd=target_folder, shell=True)
        # unpack
        subprocess.run('unzip {}.zip -d {}'.format(folder, folder), cwd=target_folder, shell=True)

    # -------------------- Prepare dataset --------------------
    # We need at least times.txt and imu.txt, both in mav0/cam0
    # times file usually comes from DSO suppv2 folder. I can just recreate it but need to make sure it doesn't change
    # anything.
    # Or I just put them in here and copy them over...
    for folder in folders:
        if not (Path(target_folder) / folder).exists():
            print("WARNING: folder {} does not exist. --> skipping.".format(folder))
            continue
        # Copy over times file from here.
        times_source = Path(__file__).parent / 'groundtruth_files' / 'euroc' / 'timesFiles' / 'mav_{}.txt'.format(
            folder)
        times_target = target_folder / folder / 'mav0' / 'cam0' / 'times.txt'
        subprocess.run('cp {} {}'.format(times_source, times_target), shell=True)

        # Create calibration file.
        calib_target = target_folder / folder / 'mav0' / 'cam0' / 'camera.txt'
        with open(calib_target, 'w') as calib_file:
            calib_file.write("458.654 457.296 367.215 248.375 -0.28340811 0.07395907 0.00019359 1.76187114e-05\n"
                             "752 480\n"
                             "crop\n"
                             "640 480\n")

        # Create IMU file. --> just remove comment lines and replace commas with spaces.
        imu_source = target_folder / folder / 'mav0' / 'imu0' / 'data.csv'
        imu_target = target_folder / folder / 'mav0' / 'cam0' / 'imu.txt'
        with open(imu_source, 'r') as source_file:
            lines = source_file.readlines()
        lines = [line.replace(',', ' ') for line in lines if not line.startswith('#')]
        with open(imu_target, 'w') as target_file:
            target_file.writelines(lines)


if __name__ == '__main__':
    main()
