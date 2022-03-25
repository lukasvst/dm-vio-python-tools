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
from utils.config_utils import read_config, read_all_configs
import subprocess
from pathlib import Path
from ruamel.yaml import YAML
from datetime import datetime
import sys
from tqdm import tqdm


class ResultsSorter:
    def __init__(self, use_commit_date=False):
        """
        :param use_commit_date: If false the time of run is used, otherwise the commit time.
        """
        self.use_commit_date = use_commit_date
        if use_commit_date:
            self.key = 'commit_time'
        else:
            self.key = 'date_run'

    def __call__(self, pair):
        setup = pair[1]
        if self.use_commit_date:
            # in this case we want to return (commit_date, run_date)
            return setup[self.key], setup['date_run']

        if self.key in setup:
            return setup[self.key]
        else:
            # Shouldn't happen.
            raise ValueError("Key does not exist.")


def create_evaluation_file(config_name, outfile, no_download, sorter, filters):
    """ Create a python evaluation file with all results from the results_folder defined in the config with the passed
    name.
    :param config_name: Name of the configuration (in configs.yaml) to use.
    :param outfile: name to evaluation file which will be created by this method.
    :param no_download:if False this method will also download results from the central server (if rsync_command is
    set in the config).
    :param sorter: Used to sort the results before writing them to file.
    :param filters: List of filters which are used to filter the results written to the evaluation file.
    """
    # Read config.
    config, config_name, general_config, _ = read_config(config_name)
    if config is None:
        print('Error: config has to specified.')
        sys.exit(1)

    general_save_folder = config['results_path']

    # Download all results from central machine.
    if not no_download:
        if 'rsync_command' in config:
            rsync_command = config['rsync_command']
            rsync_target = config['rsync_command_target']
            full_rsync_command = '{} {}/* {}/'.format(rsync_command, rsync_target, general_save_folder)
            print(full_rsync_command)
            subprocess.run(full_rsync_command, shell=True)

    # Load all results folders and read yaml files.
    all_results = load_result_yamls(Path(general_save_folder))

    # Filter and sort results based on parameters
    all_results.sort(key=sorter)

    print('There are {} results before filtering.'.format(len(all_results)))

    # Apply filters.
    filtered = all_results
    for filter_fun in filters:
        filtered = filter(filter_fun, filtered)
    filtered_results = list(filtered)

    print('There are {} results after filtering.'.format(len(filtered_results)))

    # Generate Python evaluation script.
    out_path = Path(outfile)
    write_python_eval_file(filtered_results, out_path)

    return all_results


def load_result_yamls(result_folder: Path):
    """Load the setup.yaml files for all results in the given folder."""
    yaml = YAML(typ='safe')
    all_results = []
    for child in result_folder.iterdir():
        yaml_file = child / 'setup' / 'setup.yaml'
        finished_file = child / 'setup' / 'Finished.txt'
        if not yaml_file.exists():
            print('WARNING: Skipping {}, because the setup file does not exist'.format(child))
            continue
        with open(yaml_file, 'r') as yaml_file_handle:
            settings = yaml.load(yaml_file_handle)
        finished = finished_file.exists()
        settings['finished'] = finished
        all_results.append((child, settings))
    return all_results


def write_python_eval_file(results, outfilename):
    """Write a python evaluation file with all passed results to the file with the passed name."""
    if len(results) == 0:
        return
    # Check that first line of file contains 'autogenerated' before overwriting!
    autogen_string = '# AUTOGENERATED'
    if Path(outfilename).exists():
        with open(outfilename, 'r') as outfileread:
            if not autogen_string in outfileread.readline():
                print('ERROR: Trying to overwrite file without AUTOGENERATED mark.')
                sys.exit(1)

    with open(outfilename, 'w') as outfile:
        print('Writing Python eval file.')
        outfile.write(autogen_string + '\n')

        # Init variables.
        outfile.write('from trajectory_evaluation.evaluate import evaluate_run, Dataset\n'
                      'from pathlib import Path\n'
                      'from trajectory_evaluation.plots import square_plot, results_table, line_plot\n')

        all_configs = read_all_configs()

        parent_folder = results[0][0].parent
        outfile.write("folder = '{}'\n\n".format(parent_folder))

        outfile.write(
            "print('Remember that the previous results can change names, when new results are added to the folder '\n"
            "      'and this file is recreated. It might be better to copy specific lines from this file rather '\n"
            "      'than importing the whole file.')\n\n")

        prev_setup = None

        for i, result in enumerate(results):
            # We put some information about the run in the name and comment of the result.
            # - specified name: in name (but maybe not if standard one)
            # - custom comment: in comment!
            # - Git log: In comment.
            # - Realtime result: as -RT in name
            # - dataset: in the name
            # - diff_empty -> Before Git log if not empty
            # - num_iter, only_seq -> write in name if not full run
            # - unfinished -> write in name
            folder_path, setup = result

            custom_name = '_' + setup['name']
            if custom_name == '_dsoresult' or custom_name == '_dmvioresult' or custom_name == '_orbresult' or \
                    custom_name == '_basaltresult':  # remove standard names.
                custom_name = ''
            custom_comment = ' ' + setup['comment'] if 'comment' in setup else ''
            commit_message = setup['commit_message']
            commit_message_first_line = commit_message.split('\n')[0]  # Commit message could contain line breaks.
            noimu_bool = 'noimu' in setup and setup['noimu']
            noimu = '_noimu' if noimu_bool else ''
            realtime = '_RT' if 'realtime' in setup and setup['realtime'] else ''
            config_name = setup['config_name']
            short_name = all_configs[config_name]['short_name'] if config_name in all_configs else config_name
            dataset_name = setup['dataset']
            dataset_config = all_configs['config_general'][dataset_name]
            diff_string = '+DIFF ' if not setup['diff_empty'] else ''
            default_iter = dataset_config['default_iter']
            partial_string = '_part' if setup['num_iter'] < default_iter or not setup['only_seq'] is None else ''
            unfinished_string = '_unfin' if setup['finished'] is False else ''
            withgui_string = '_withgui' if 'withgui' in setup and setup['withgui'] else ''
            quiet_string = '_quiet' if 'quiet' in setup and setup['quiet'] else ''
            output_type_string = ' output=' + setup['output_type'] if 'output_type' in setup else ''
            custom_args_string = setup['custom_dso_args'] if 'custom_dso_args' in setup else ''
            if 'custom_dmvio_args' in setup:
                custom_args_string = setup['custom_dmvio_args']
            is_orb_result = 'orbslam' in setup and setup['orbslam']
            if custom_args_string != '':
                custom_args_string = ' ' + custom_args_string
            settings_string = setup['dso_settings'] if 'dso_settings' in setup else ''
            if 'dmvio_settings' in setup:
                settings_string = setup['dmvio_settings']
            if settings_string != '':
                settings_string = ' settings=' + settings_string
            is_basalt_result = 'basalt' in setup and setup['basalt']
            if is_basalt_result:
                settings_string = ' config={} calib={}'.format(setup['basalt_config'], setup['basalt_calib'])
            build_type_string = ''
            if 'build_type' in setup:
                build_type = setup['build_type']
                if build_type != 'RelWithDebInfo':
                    build_type_string = '_' + build_type

            res_name = str(
                i) + custom_name + noimu + realtime + '_' + dataset_name + '_' + short_name + build_type_string + \
                       partial_string + unfinished_string
            if is_orb_result:
                res_name = 'orb' + res_name
            elif is_basalt_result:
                res_name = 'basalt' + res_name
            comment = custom_comment + diff_string + settings_string + custom_args_string + ' ' + \
                      commit_message_first_line
            visname = res_name + custom_comment + ':' + output_type_string + quiet_string + withgui_string + \
                      settings_string + custom_args_string + ' ' + diff_string + commit_message_first_line
            visname = visname.replace("'", '"')

            if 'tumvi' in dataset_name:
                dataset_arg = 'Dataset.tumvi'
            elif '4seasons' in dataset_name:
                dataset_arg = 'Dataset.four_seasons'
            elif 'euroc' in dataset_name:
                dataset_arg = 'Dataset.euroc'
            else:
                raise ValueError("ERROR: Unknown dataset")

            # Write newline if different commit hash than previous.
            if not prev_setup is None and setup['git_hash'] != prev_setup['git_hash']:
                outfile.write('\n')

            outfile.write("#{}\n".format(comment))
            outfile.write(
                "res{}, gtscale_{} = evaluate_run(Path(folder) / '{}', {}, {}, '{}')\n".format(res_name, res_name,
                                                                                               folder_path.name,
                                                                                               dataset_arg,
                                                                                               setup['num_iter'],
                                                                                               visname))

            prev_setup = setup


def finished_or_temp_filter(pair):
    setup = pair[1]
    if setup['finished']:
        return True
    if 'temporary' in setup and setup['temporary'] is True:
        return True
    return False


def full_filter(pair):
    setup = pair[1]
    all_configs = read_all_configs()
    dataset_name = setup['dataset']
    dataset_config = all_configs['config_general'][dataset_name]
    default_iter = dataset_config['default_iter']
    if setup['num_iter'] < default_iter or not setup['only_seq'] is None:
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Create Python evaluation file. It will also evaluate all results which have not been evaluated '
                    'yet.')
    parser.add_argument('--config', type=str, default=None, help="Config to use.")
    parser.add_argument('--outfile', type=str, default='evaluations.py',
                        help='Name of the resulting python evalution file. By default stored in the folder specified '
                             'in configs.yaml')
    parser.add_argument('--no_download', default=False, action='store_true',
                        help="Don't download from central storage before creating the evaluation file.")
    parser.add_argument('--evaluate', default=False, action='store_true',
                        help="If passed this script will compute all results (which can take a while). Otherwise "
                             "results will only be computed on demand when using the written evaluation script.")
    parser.add_argument('--force_evaluate', default=False, action='store_true',
                        help="Re-evaluate all results even if they have already been evaluated before")
    args = parser.parse_args()

    sorter = ResultsSorter(use_commit_date=True)  # You can first use commit date for sorting or just the run date.
    finished_filter = lambda pair: pair[1]['finished'] is True

    # Example date filter below.
    date = datetime.strptime('03.12.20 17:25:00', '%d.%m.%y %H:%M:%S')
    date_filter = lambda pair: pair[1]['date_run'] > date

    all_results = create_evaluation_file(args.config, args.outfile, args.no_download, sorter, [finished_filter])

    # Example: Use this to save only full evaluations.
    # all_results = create_evaluation_file(args.config, 'evaluations_only_full.py', True, sorter,
    #                                      [finished_filter, full_filter])

    if args.evaluate or args.force_evaluate:
        print("Pre-evaluating all results which have not been evaluated yet.")
        for pair in tqdm(all_results, leave=True):
            from trajectory_evaluation.evaluate import evaluate_with_config
            result, result_gt_scaled = evaluate_with_config(pair, args.force_evaluate)


if __name__ == "__main__":
    main()
