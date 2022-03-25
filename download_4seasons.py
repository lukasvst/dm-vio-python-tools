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
from tqdm import tqdm
from ruamel.yaml import YAML
from utils.config_utils import read_config, replace_dataset_in_config, shall_replace_dataset_in_config
import argparse
from utils.prepare_4seasons import prepare4seasons


def main():
    parser = argparse.ArgumentParser(
        description='Download all (or just one) sequences of the 4Seasons dataset and prepare them for use with '
                    'DM-VIO (interpolate IMU files, convert groundtruth files, etc.). Also write the path to the '
                    'dataset to the config file.')
    parser.add_argument('--folder', type=str, help='Location where the dataset shall be downloaded to.', required=True)
    parser.add_argument('--only_seq', default=None, type=int,
                        help='Only download one sequence (with the given index starting with 0).')
    parser.add_argument('--no_download', default=False, action='store_true',
                        help="Don't download but only prepare already downloaded sequences. Assumes that the dataset "
                             "has been downloaded (but not prepared for DM-VIO).")
    parser.add_argument('--crop_images', default=False, action='store_true',
                        help='Also crop images, to make the config 4seasonsCR work. Mainly important for evaluation '
                             'of other methods, as DM-VIO will use runtime-cropped images anyway with the default '
                             'config 4seasons.')
    parser.add_argument('--accept_license', default=False, action='store_true',
                        help='Accept license of 4seasons dataset (for machines with no interactive commandline input. '
                             'Only select if you agree to the terms of the dataset!')
    args = parser.parse_args()

    yaml = YAML()
    config, config_name, general_config, all_configs = read_config(None, yaml)
    if config is None:
        print('Error: There is no default config for this machine yet. Have you called create_config.py yet?')
        return

    target_folder = Path(args.folder)

    will_replace_dataset_in_config = shall_replace_dataset_in_config(config, '4seasons', target_folder)

    if not target_folder.exists():
        target_folder.mkdir()

    # -------------------- Ask for license --------------------
    print(" The 4Seasons dataset is copyright by Artisense and published under the\n"
          "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) License.\n"
          "This means that you must attribute the work in the manner specified by the authors, you may not use this "
          "work for\n"
          "commercial purposes and if you alter, transform, or build upon this work, you may distribute the resulting "
          "work only\n"
          "under the same license. Per GDPR  requirements, to download and use the data you need to register and "
          "specify the\n"
          "intended purpose of using the dataset: "
          "https://vision.cs.tum.edu/webshare/g/4seasons-dataset/html/form.php\n\n"

          "Exclusive commercial rights for the 4Seasons dataset are held by Artisense. For commercial licensing of "
          "the dataset please contact licensing@artisense.ai.\n\n"

          "4Seasons Dataset Terms of Use\n\n"

          "\t Researcher shall use the dataset only for non-commercial research and educational purposes.\n"
          "\t Artisense/TUM make no representations or warranties regarding the dataset, including but not limited to "
          "warranties of non-infringement or fitness for a particular purpose.\n"
          "\t Researcher accepts full responsibility for his or her use of the dataset and shall defend and indemnify "
          "Artisense/TUM including their employees, Trustees, officers and agents, against any and all claims arising "
          "from Researcher's use of the dataset, including but not limited to Researcher's use of any copies that he "
          "or she may create from the dataset.\n"
          "\t Artisense/TUM reserves the right to terminate Researcher's access to the dataset at any time.\n"
          "\t The law of the Germany apply to all disputes under this agreement.\n")

    if args.accept_license:
        print("License has been accepted with commandline argument.")
    else:
        char = input("Please agree to the 4Seasons Dataset terms of use by typing: y(es)").lower()
        if char != 'y' and char != 'yes':
            print("License has not been accepted. Exiting.")
            return

    # First download calibration
    calibration_folder = Path(target_folder) / 'calibration'
    if not (calibration_folder.exists()):
        subprocess.run('wget https://vision.cs.tum.edu/webshare/g/4seasons-dataset/calibration/calibration.zip',
                       cwd=target_folder, shell=True)
        subprocess.run('unzip calibration.zip', cwd=target_folder, shell=True)

    # We rename the sequence from 'recording_date' to 'name_date'
    folders = [('office', '2021-01-07_12-04-03'),
               ('office', '2021-02-25_13-51-57'),
               ('office', '2020-03-24_17-36-22'),
               ('office', '2020-03-24_17-45-31'),
               ('office', '2020-04-07_10-20-32'),
               ('office', '2020-06-12_10-10-57'),
               ('neighbor', '2020-10-07_14-47-51'),
               ('neighbor', '2020-10-07_14-53-52'),
               ('neighbor', '2020-12-22_11-54-24'),
               ('neighbor', '2021-02-25_13-25-15'),
               ('neighbor', '2020-03-26_13-32-55'),
               ('neighbor', '2021-05-10_18-02-12'),
               ('neighbor', '2021-05-10_18-32-32'),
               ('business', '2021-01-07_13-12-23'),
               ('business', '2021-02-25_14-16-43'),
               ('business', '2020-10-08_09-30-57'),
               ('country', '2020-10-08_09-57-28'),
               ('country', '2021-01-07_13-30-07'),
               ('country', '2020-04-07_11-33-45'),
               ('country', '2020-06-12_11-26-43'),
               ('city', '2020-12-22_11-33-15'),
               ('city', '2021-01-07_14-36-17'),
               ('city', '2021-02-25_11-09-49'),
               ('oldtown', '2020-10-08_11-53-41'),
               ('oldtown', '2021-01-07_10-49-45'),
               ('oldtown', '2021-02-25_12-34-08'),
               ('oldtown', '2021-05-10_21-32-00'),
               ('parking', '2020-12-22_12-04-35'),
               ('parking', '2021-02-25_13-39-06'),
               ('parking', '2021-05-10_19-15-19')
               ]

    only_seq = args.only_seq
    if not only_seq is None:
        folders = [folders[only_seq]]  # only download this sequence

    # Insert into config
    if will_replace_dataset_in_config:
        replace_dataset_in_config(config, '4seasons', target_folder)
        if args.crop_images:
            if shall_replace_dataset_in_config(config, '4seasonsCR', target_folder):
                replace_dataset_in_config(config, '4seasonsCR', target_folder)
        print("Saving updated config.")
        with open('configs.yaml', 'w') as config_file:
            yaml.dump(all_configs, config_file)

    command_general = "wget https://vision.cs.tum.edu/webshare/g/4seasons-dataset/dataset/"

    # -------------------- Download! --------------------
    if not args.no_download:
        for name, date in tqdm(folders):
            down_name = 'recording_' + date
            new_name = name + '_' + date

            targ_folder = Path(target_folder) / new_name
            if targ_folder.exists():
                print('Skipping: {}'.format(new_name))
                continue
            targ_folder.mkdir()

            postfixes = ['_imu_gnss.zip', '_stereo_images_undistorted.zip', '_reference_poses.zip', '_point_clouds.zip']
            for postfix in postfixes:
                file_name = down_name + postfix
                command1 = '{}{}/{}'.format(command_general, down_name, file_name)
                subprocess.run(command1, cwd=targ_folder, shell=True)
                subprocess.run('unzip {}'.format(file_name), cwd=targ_folder, shell=True)

                subprocess.run('mv {}/* .'.format(down_name), cwd=targ_folder, shell=True)
                Path(targ_folder / down_name).rmdir()
                subprocess.run('rm ' + str(Path(targ_folder / file_name)), cwd=targ_folder, shell=True)

    # -------------------- Prepare dataset (interpolate IMU files, convert groundtruth, etc.)! --------------------
    groundtruth_save_folder = target_folder / "groundtruth"
    if not groundtruth_save_folder.exists():
        groundtruth_save_folder.mkdir()

    renamed_folders = [name + '_' + date for name, date in folders]
    prepare4seasons(target_folder, groundtruth_save_folder, renamed_folders, general_preparation=True,
                    create_cropped_images=args.crop_images)


if __name__ == '__main__':
    main()
