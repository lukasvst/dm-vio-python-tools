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
from pathlib import Path
from datetime import datetime
from ruamel.yaml import YAML
import sys


def get_git_log_and_diff(repository_path, git_diff_save_path):
    # Get Git log
    git_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repository_path).strip().decode('ascii')
    commit_message = subprocess.check_output(['git', 'log', '--format=%B', '-n', '1'],
                                             cwd=repository_path).strip().decode('ascii')
    # unfortunately the commit_time is in utc (and not in local time like the running time), but as we want to use it
    # for sorting mainly that should be okay.
    commit_time = datetime.utcfromtimestamp(
        int(subprocess.check_output(['git', 'log', '--format=%ct', '-n', '1'], cwd=repository_path).strip().decode(
            'ascii')))

    diff_is_empty = None  # undefined unless git_diff_save_path is given.
    if not git_diff_save_path is None:
        # Save git_diff
        subprocess.run('git diff > ' + str(git_diff_save_path), cwd=repository_path, shell=True)
        diff_is_empty = git_diff_save_path.stat().st_size == 0

    return git_hash, commit_message, diff_is_empty, commit_time


def save_setup(setup, setup_save_folder, dmvio_folder, config, commands):
    # - Git log (also of these tools), git diff, PC Config (on Ubuntu, also automatic apt list), parameters,
    git_diff_save_path = setup_save_folder / 'git_diff.txt'
    git_hash, commit_message, diff_is_empty, commit_time = get_git_log_and_diff(dmvio_folder, git_diff_save_path)

    # Also save git_log and diff  of evaluation tools
    eval_diff_save_path = setup_save_folder / 'eval_tools_git_diff.txt'
    git_hash_eval_tools, commit_message_eval_tools, diff_is_empty_eval_tools, _ = get_git_log_and_diff(
        Path(__file__).parent, eval_diff_save_path)

    # Save yaml with setup .
    setup_file = setup_save_folder / 'setup.yaml'
    auto_setup = {
        'git_hash': git_hash,
        'commit_message': commit_message,
        'commit_time': commit_time,
        'diff_empty': diff_is_empty,
        'eval_tool_command': " ".join(sys.argv),
        'eval_tools_git_hash': git_hash_eval_tools,
        'eval_tools_commit_message': commit_message_eval_tools,
        'eval_tools_diff_empty': diff_is_empty_eval_tools,
    }
    setup.update(auto_setup)

    # Save commands which will be run.
    for i, command in enumerate(commands):
        setup['command_{}'.format(i)] = command.command
        setup['cwd{}'.format(i)] = str(command.working_dir)

    print(setup)

    yaml = YAML()
    with open(setup_file, 'w') as setup_file_handle:
        # yaml.dump(setup, setup_file_handle, sort_keys=False)
        yaml.dump(setup, setup_file_handle)

    # Save PC Config
    # Copy manual config:
    config_path = setup_save_folder / 'pcconfig.txt'
    manual_config_path = config['pc_config_path']
    pc_config_command = config['pc_config_command']
    if not manual_config_path is None:
        subprocess.run('cp {} {}'.format(manual_config_path, config_path), shell=True)
    if not pc_config_command is None:
        # This runs apt list >> pcconfig.txt on Linux
        subprocess.run('{} >> {}'.format(pc_config_command, config_path), shell=True)
