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

import argparse
from pathlib import Path
from utils.config_utils import read_config
import subprocess
from sys import platform
from ruamel.yaml import YAML


def main():
    parser = argparse.ArgumentParser(
        description='Create configuration for DM-VIO in configs.yaml. Make it the default configuration for this '
                    'machine.')
    parser.add_argument('--name', type=str,
                        help='Name of this configuration (e.g. workpc, homepc, etc.). Useful when multiple machines '
                             'are in use for running DM-VIO.',
                        required=True)
    parser.add_argument('--dmvio_folder', type=str, help='Path to location where the source code of DM-VIO was cloned.',
                        required=True)
    parser.add_argument('--results_folder', type=str,
                        help='The results of running DM-VIO will be stored in this folder.', required=True)
    parser.add_argument('--realtime', action='store_true', help='Evaluate in realtime mode.')
    args = parser.parse_args()

    yaml = YAML()
    config, config_name, general_config, all_configs = read_config(None, yaml)
    replace_default_config = True
    if not config is None:
        char = input(
            "Note: There is already a default configuration for this machine. Do you want to make the new "
            "configuration the new default? y(es), n(yo), c(ancel)").lower()
        if char == 'y' or char == 'yes':
            replace_default_config = True
        elif char == 'n' or char == 'no':
            replace_default_config = False
        else:
            print("Exiting.")
            return

    name = args.name
    if name in all_configs:
        print("Error, config with name {} already exists".format(name))
        return

    print("Testing command for documenting program version when running code.")
    pc_config_command = ''
    # Find out platform to insert PC documentation command.
    if platform == "linux" or platform == "linux2":
        pc_config_command = 'apt list'
    elif platform == "darwin":
        pc_config_command = 'brew list --versions'
    elif platform == "win32":
        pc_config_command = ''
    # test if it works
    result_pc_config = subprocess.run('{} > /dev/null 2>&1'.format(pc_config_command), shell=True)
    if result_pc_config.returncode != 0:
        print('Command for documenting program versions doesnt work.')
        pc_config_command = ''

    config = {
        'short_name': name,
        'dmvio_folder': args.dmvio_folder,
        'pc_config_path': None,
        'pc_config_command': pc_config_command,
        'slurm': False,
        'results_path': args.results_folder,
    }

    all_configs[name] = config
    all_configs.move_to_end(name, False)

    # Create results folder if it doesn't exist.
    results_path = Path(args.results_folder)
    if not results_path.exists():
        results_path.mkdir()

    print("Saving updated config.")
    with open('configs.yaml', 'w') as config_file:
        yaml.dump(all_configs, config_file)

    if replace_default_config:
        with open(Path(__file__).parent / 'defaultconfig.txt', 'w') as default_config_file:
            default_config_file.write(name)


if __name__ == "__main__":
    main()
