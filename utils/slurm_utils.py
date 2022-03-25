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

import math
import subprocess


def execute_commands_slurm(commands, setup_folder, memory, time, mail_type, num_tasks, num_nodes_passed):
    sbatch_filename = setup_folder / 'runscript.sbatch'
    num_commands = len(commands)
    if not num_tasks is None:
        num_commands = num_tasks
    tasks_per_node = 10
    num_nodes = math.ceil(float(num_commands) / float(tasks_per_node))
    if not num_nodes_passed is None:
        num_nodes = num_nodes_passed
    with open(sbatch_filename, 'w') as sbatch:
        init_lines = [
            '#!/bin/bash',
            '#SBATCH --job-name="DM-VIO Run"',
            '#SBATCH --nodes={}'.format(num_nodes),
            '#SBATCH --ntasks={}'.format(num_commands),
            '#SBATCH --cpus-per-task=1',
            '#SBATCH --mem-per-cpu={}'.format(memory),
            '#SBATCH --time={}'.format(time),
            '#SBATCH --mail-type={}'.format(mail_type),
            '#SBATCH --output=/path/to/console/output/slurm-%j.out',
            '#SBATCH --error=/path/to/error/logs/slurm-%j.out'
        ]
        add_newlines = lambda x: x + '\n'
        init_lines = map(add_newlines, init_lines)
        sbatch.writelines(init_lines)
        sbatch.write('\n')

        command_prefix = 'srun --exclusive --ntasks 1 --nodes 1'
        command_lines = []
        for command in commands:
            command_lines.append('cd {}'.format(command.working_dir))
            full_comm = '{} {} &'.format(command_prefix, command.command)
            command_lines.append("echo Executing '{}'".format(full_comm))
            command_lines.append(full_comm)

        command_lines = map(add_newlines, command_lines)
        sbatch.writelines(command_lines)
        sbatch.write('\n')
        sbatch.write('wait')
        sbatch.write('\n')

        move_lines = []
        for command in commands:
            move_lines.extend([move_command for move_command in command.post_run_commands])
        move_lines = map(add_newlines, move_lines)
        sbatch.writelines(move_lines)
        sbatch.write('echo Finished > {}\n'.format(setup_folder / 'Finished.txt'))
    print('Starting sbatch file {}'.format(sbatch_filename))
    subprocess.run('sbatch {}'.format(sbatch_filename), shell=True)
