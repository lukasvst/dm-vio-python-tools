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
        description='Download all (or just one) sequences of the TUM-VI dataset and write the path to them to the '
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
        "Please note: The TUM-VI dataset was created by D. Schubert, T. Goll, N. Demmel, V. Usenko, J. Stueckler and "
        "D. Cremers \n and is licensed under a Creative Commons 4.0 Attribution License (CC BY 4.0). For more "
        "information please see https://vision.in.tum.de/data/datasets/visual-inertial-dataset.\n"
        "This download code was not provided by the authors, so no warranty is given that it works as expected.")

    target_folder = Path(args.folder)

    will_replace_dataset_in_config = shall_replace_dataset_in_config(config, 'tumvi', target_folder)

    if not target_folder.exists():
        target_folder.mkdir()

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

    only_seq = args.only_seq
    if not only_seq is None:
        folders = [folders[only_seq]]  # only download this sequence

    # Insert into config
    if will_replace_dataset_in_config:
        replace_dataset_in_config(config, 'tumvi', target_folder)
        print("Saving updated config.")
        with open('configs.yaml', 'w') as config_file:
            yaml.dump(all_configs, config_file)

    command_general = 'wget -4 https://cdn3.vision.in.tum.de/tumvi/exported/euroc/512_16/'
    for folder in folders:
        if (target_folder / folder).exists():
            print('Folder exists --> skipping sequence {}'.format(folder))
            continue
        command = '{}{}.tar'.format(command_general, folder)
        subprocess.run(command, cwd=target_folder, shell=True)
        subprocess.run(command + '.md5', cwd=target_folder, shell=True)

    # Check md5 sums:
    subprocess.run('md5sum -c *.md5', cwd=target_folder, shell=True)

    # Unpack all
    for folder in folders:
        if (target_folder / folder).exists():
            continue
        subprocess.run('tar -xvf {}.tar'.format(folder), cwd=target_folder, shell=True)


if __name__ == '__main__':
    main()
