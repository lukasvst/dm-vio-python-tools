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
import numpy as np


def offset_times(array, offset):
    for line in array:
        line[0] = str(int(line[0]) + offset)


def interpolate_imu_file(imu_input_filename, times_input_filename, imu_output_filename):
    """Inserts interpolated IMU measurements at all timestamps of images."""
    with open(imu_input_filename) as imu_input_file:
        imu_lines = imu_input_file.readlines()
        imu_lines = [line.rstrip('\n').split(' ') for line in imu_lines]
        imu_time0 = int(imu_lines[0][0])
        # We want to use np.interp but it cannot handle the long timestamps. So we subtract the timestamp of the first
        # imu data from all timestamps and will add them back later.
        offset_times(imu_lines, -imu_time0)
        imu_data = np.array(imu_lines, dtype=float)

    with open(times_input_filename) as times_input_file:
        times_lines = times_input_file.readlines()
        times_lines = [line.rstrip('\n').split(' ') for line in times_lines]
        offset_times(times_lines, -imu_time0)
        times_data = np.array(times_lines, dtype=float)

    image_times = times_data[:, 0]
    imu_times = imu_data[:, 0]
    min_imu_time = imu_data[0, 0]
    max_imu_time = imu_data[imu_data.shape[0] - 1, 0]

    filtered_times = image_times[np.logical_and(image_times <= max_imu_time, image_times >= min_imu_time)]

    all_times = np.concatenate((filtered_times, imu_times), axis=0)
    all_times.sort()

    interpolated = [np.interp(all_times, imu_times, imu_data[:, i + 1]) for i in range(6)]
    interpolated.insert(0, all_times)
    interpolated_stacked = np.stack(interpolated).transpose()

    with open(imu_output_filename, 'w') as out_file:
        outlist = interpolated_stacked.tolist()
        offset_times(outlist, imu_time0)  # add back the offset.
        outlines = [(' '.join([elem if type(elem) is str else '{:f}'.format(elem) for elem in line]) + '\n') for line in
                    outlist]
        out_file.writelines(outlines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Interpolate IMU data to have a 'fake' measurement at each time in the times file.")
    parser.add_argument('--input', type=str, default=None, help="Path to IMU input file.")
    parser.add_argument('--times', type=str, default=None, help="Path to input times file.")
    parser.add_argument('--output', type=str, default=None, help="Path to output file.")
    args = parser.parse_args()
    interpolate_imu_file(args.input, args.times, args.output)
