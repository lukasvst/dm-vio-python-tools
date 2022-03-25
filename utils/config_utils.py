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

from ruamel.yaml import YAML
from pathlib import Path


def read_all_configs(yaml=None):
    """Read all configs from configs.yaml"""
    with open('configs.yaml', 'r') as config_file:
        if yaml is None:
            yaml = YAML()
        all_configs = yaml.load(config_file)
    return all_configs


def read_config(config_name, yaml=None):
    """Read the config with the specified name from configs.yaml. config_name can also be None, then the default
    config will be used."""
    all_configs = read_all_configs(yaml)
    if config_name is None:
        # Maybe it's specified via file defaultconfig.txt
        try:
            with open('defaultconfig.txt', 'r') as file:
                lines = file.readlines()
                config_name = lines[0].rstrip('\n')
        except IOError:
            return None, None, None, all_configs
    config = all_configs[config_name]
    general_config = all_configs['config_general']
    return config, config_name, general_config, all_configs


def input_custom_variables(string: str, dmvio_folder: str):
    """ Replace the following environment variables in the given string.
    if ${EVALPATH} is inside string it is replaced with the path to the evaltools (the folder where this file is
    located).
    ${DMVIO_PATH} is replaced with the path to DM-VIO.
    """
    return string.replace('${EVALPATH}', str(Path(__file__).parent.parent.resolve())).replace('${DMVIO_PATH}',
                                                                                              dmvio_folder)


def shall_replace_dataset_in_config(config, dataset_name, target_folder):
    replace_dataset_in_config = True
    if dataset_name in config and 'dataset_path' in config[dataset_name]:
        prev_folder = Path(config[dataset_name]['dataset_path'])
        if prev_folder != target_folder:
            char = input(
                "A path to this dataset is already in the config at {}. Overwrite it? y(es), n(yo), c(ancel)").lower()
            if char == 'y' or char == 'yes':
                replace_dataset_in_config = True
            elif char == 'n' or char == 'no':
                replace_dataset_in_config = False
            else:
                print("Exiting.")
                import sys
                sys.exit()
    return replace_dataset_in_config


def replace_dataset_in_config(config, dataset_name, target_folder):
    if not dataset_name in config:
        config[dataset_name] = dict()
    config[dataset_name]['dataset_path'] = str(target_folder)
    if not 'results_path' in config[dataset_name]:
        config[dataset_name]['results_path'] = config['results_path']
