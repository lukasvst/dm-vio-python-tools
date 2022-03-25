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

from enum import Enum
from pathlib import Path
import trajectory_evaluation.evaluate_ate as evaluate_ate
import trajectory_evaluation.associate as associate
import numpy as np
from ruamel.yaml import YAML
from tqdm import tqdm


class Dataset(Enum):
    euroc = 0
    tumvi = 1
    four_seasons = 2


class EvalResults:
    """Stores the results (rmse, etc.) of the evaluation for further analysis.
    run_folder
        path to the results folder.
    folder_names
        names of all the sequences of the dataset evaluated on.
    errors : np.array(num_iter x num_sequences)
        rmse (absolute trajectory error) for each run
    scales : np.array(num_iter x num_sequences)
        the estimated scale for each run.
    scale_errors : np.array(num_iter x num_sequences)
        scale error (in percentage) for each run.
    percentage_done : np.array(num_iter x num_sequences)
        for each run the percentage of the sequence completed.
    name : str
        name of the result for plot legend, can be None.
    median_errors : np.array(num_sequences)
        median rmse (ate) for each sequence.
    median_scale_errors : np.array(num_sequences)
        scale error of the median run (in terms of rmse) for each sequence.
    median_index : np.array(num_sequences)
        index of the median result (in terms of rmse) for each sequence. If num_iter is even this will be the middle
        result with larger error.
    """

    def __init__(self, run_folder, folder_names, errors, scales, scale_errors, percentage_done, dataset: Dataset):
        self.run_folder = run_folder
        self.folder_names = folder_names
        self.errors = errors
        self.scales = scales
        self.scale_errors = scale_errors
        self.percentage_done = percentage_done
        self.name = None
        self.dataset = dataset

        self.num_iter = errors.shape[0]

        # Compute median results.
        self.median_errors = np.median(errors, axis=0)

        # Note: When even we use the worse of the middle results.
        self.median_index = np.argsort(errors, axis=0)[errors.shape[0] // 2, :]
        # We don't save median scale, but the scale of the median result (according to rmse).
        # The reason is that we think it makes more sense to sort results based on rmse than on scale error, but
        # probably both would be fine.
        self.median_scale_errors = np.take_along_axis(scale_errors, self.median_index[None, :], axis=0).flatten()


def evaluate_with_config(pair, always_reevaluate=False):
    """
    Evaluate a run (compute rmse, scale_error, etc.) for all sequences. If already evaluated it will just load the
    results from file.
    :param pair: one entry in the list computed by load_result_yamls (first folder, then loaded config).
    :param always_reevaluate: If true the results will be re-evaluated even if results have already been saved to file.
    :return: result (uses estimated scale), result_gt_scaled (uses groundtruth scale); both of type EvalResults.
    """
    folder, setup = pair

    dataset_name = setup['dataset']
    noimu_bool = 'noimu' in setup and setup['noimu']

    if 'tumvi' in dataset_name:
        dataset = Dataset.tumvi
    elif '4seasons' in dataset_name:
        dataset = Dataset.four_seasons
    elif 'euroc' in dataset_name:
        dataset = Dataset.euroc
    else:
        raise ValueError("ERROR: Unknown dataset")

    return evaluate_run(folder, dataset, setup['num_iter'], None, always_reevaluate)


def evaluate_run(run_folder: Path, dataset: Dataset, num_iter: int, name=None, always_reevaluate=False) -> (
        EvalResults, EvalResults):
    """Evaluate all sequences and iterations of a run and save it to file (and return it).
    If the evaluation result has already been saved to file it will just load it.
        returns

    :param run_folder: Folder of the run which will be evaluated.
    :param dataset: Dataset to evaluate on.
    :param num_iter: Number of iterations this run used.
    :param name: Name which will be stored in the returned results.
    :param always_reevaluate: If true the results will be re-evaluated even if results have already been saved to file.
    :return: result (uses estimated scale), result_gt_scaled (uses groundtruth scale); both of type EvalResults.
    """
    np.set_printoptions(precision=3, suppress=True)
    # First check if result already exists.
    if not always_reevaluate:
        result, result_gt_scale = load_eval_results_from_folder(run_folder, dataset)
        if not result is None:
            print('Loaded pre-evaluated results from file.')
            if not name is None:
                result.name = name
                result_gt_scale.name = 'gt_scale_' + name
            return result, result_gt_scale

    print("Evaluating now.")

    sequences, time_threshold = get_groundtruth_data(dataset)

    # Rows are iterations, columns are sequences.
    all_percentage_done = np.zeros((num_iter, len(sequences)))
    all_rmse = np.ones((num_iter, len(sequences))) * np.inf
    all_scales = np.ones((num_iter, len(sequences))) * np.inf
    all_scale_errors = np.ones((num_iter, len(sequences))) * np.inf

    all_rmse_gt_scaled = np.ones((num_iter, len(sequences))) * np.inf
    all_gt_scales = np.ones((num_iter, len(sequences))) * np.inf

    for i, sequence in enumerate(tqdm(sequences, leave=False)):
        for iter in range(num_iter):
            results_file = run_folder / 'results' / '{}_{}.txt'.format(sequence.folder, iter)
            if results_file.exists():
                # Read scale to use from scale file.
                scale_file = run_folder / '{}_{}'.format(sequence.folder, iter) / 'scalesdso.txt'
                if not scale_file.exists():
                    print("WARNING: No scale file exists --> assuming scale of 1.")
                    scale = 1.0
                else:
                    try:
                        scale = get_estimated_scale(scale_file)
                    except IndexError:
                        print("WARNING: Could not get scale for result {}. --> Skipping.".format(results_file))
                        continue

                result, result_gt_scale, min_and_max_time = evaluate_ate.compute_ate_fast(sequence.groundtruth_data,
                                                                                          results_file, scale, 0.05,
                                                                                          allow_unassociated=(
                                                                                                  dataset !=
                                                                                                  Dataset.euroc))

                # Compute percentage of the sequence completed and invalidate result if it is too low.
                percentage_done = (min_and_max_time[1] - min_and_max_time[0]) / sequence.duration
                # Enforce that incomplete sequences don't count as success.
                if percentage_done < time_threshold:
                    if not result is None:
                        result.rmse = float('inf')
                    result_gt_scale.rmse = float('inf')
                all_percentage_done[iter, i] = percentage_done
                all_rmse[iter, i] = result.rmse
                all_scales[iter, i] = result.scale
                all_scale_errors[iter, i] = get_scale_error(result.scale, result_gt_scale.scale)
                all_rmse_gt_scaled[iter, i] = result_gt_scale.rmse
                all_gt_scales[iter, i] = result_gt_scale.scale
            else:
                print('WARNING: Skipping because does not exist: {}'.format(results_file))

    folder_names = [sequence.folder for sequence in sequences]
    result = EvalResults(run_folder, folder_names, all_rmse, all_scales, all_scale_errors, all_percentage_done, dataset)
    result_gt_scale = EvalResults(run_folder, folder_names, all_rmse_gt_scaled, all_gt_scales,
                                  np.zeros((num_iter, len(sequences))), all_percentage_done, dataset)

    # Save result.
    save_results_to_folder(run_folder, result, result_gt_scale)

    if not name is None:
        result.name = name
        result_gt_scale.name = 'gt_scale_' + name

    return result, result_gt_scale


def get_scale_error(estimated_scale, gt_scale):
    scale_err = gt_scale / estimated_scale

    # Note that we do not use the more simple formulation of
    # scale_err_simple = abs(gt_scale / estimated_scale - 1)
    # The simple formulation can only a get a maximum scale error of 100% in one direction,
    # whereas ours is symmetric (in the way that a too large and a too small scale both have the same effect).
    # For small scale errors as present in most evaluations they are very similar though, so in practice it only makes
    # a small difference.

    if scale_err < 1:
        scale_err = 1.0 / scale_err
    scale_err = scale_err - 1

    # return in percentage.
    return scale_err * 100


def get_estimated_scale(scale_filename):
    """Read the estimated scale from file."""
    with open(scale_filename) as scale_file:
        lines = scale_file.readlines()
    # We use the latest estimated scale.
    return float(lines[-1].split(' ')[1])


def load_eval_results_from_folder(folder: Path, dataset: Dataset):
    """ if EvalResults have been stored to file they will be read by this method."""
    filename = folder / 'setup' / 'evaluation_results.txt'
    if not filename.exists():
        return None, None

    try:
        yaml = YAML()
        with open(filename, 'r') as results_file:
            eval_results = yaml.load(results_file)

        folder_names = eval_results['folder_names']
        results = eval_results['results']
        results_gt_scale = eval_results['results_gt_scale']
        results_out = EvalResults(folder, folder_names, np.array(results['errors']), np.array(results['scales']),
                                  np.array(results['scale_errors']), np.array(results['percentage_done']), dataset)
        results_gt_scale_out = EvalResults(folder, folder_names, np.array(results_gt_scale['errors']),
                                           np.array(results_gt_scale['scales']),
                                           np.array(results_gt_scale['scale_errors']),
                                           np.array(results_gt_scale['percentage_done']), dataset)
    except KeyError:
        return None, None

    return results_out, results_gt_scale_out


def save_results_to_folder(folder: Path, results: EvalResults, results_gt_scale: EvalResults):
    """Save the evaluation results to file."""
    filename = folder / 'setup' / 'evaluation_results.txt'

    res = {
        'folder_names': results.folder_names,
        'results': {
            'errors': results.errors.tolist(),
            'scales': results.errors.tolist(),
            'scale_errors': results.scale_errors.tolist(),
            'percentage_done': results.percentage_done.tolist()
        },
        'results_gt_scale': {
            'errors': results_gt_scale.errors.tolist(),
            'scales': results_gt_scale.errors.tolist(),
            'scale_errors': results_gt_scale.scale_errors.tolist(),
            'percentage_done': results_gt_scale.percentage_done.tolist()
        }
    }

    yaml = YAML()
    with open(filename, 'w') as results_file:
        yaml.dump(res, results_file)


class GroundtruthDataForSequence:
    def __init__(self, folder, start_time, end_time, times_file, groundtruth_file):
        self.folder = folder
        self.start_time = start_time
        self.end_time = end_time
        self.times_file = times_file
        self.groundtruth_file = groundtruth_file

        # Preload GT data.
        self.groundtruth_data = associate.read_file_list(self.groundtruth_file)

        # Read times data
        with open(self.times_file) as times_file_handle:
            times_lines = times_file_handle.readlines()
        self.times = [float(line.split(' ')[1]) for line in times_lines if not line.startswith('#')]

        # start_time and end_time are the start and end frame (starting with 0). These are the times for them.
        real_start_time = self.times[start_time]
        real_end_time = self.times[-1] if end_time is None else self.times[end_time]
        self.duration = real_end_time - real_start_time


def get_groundtruth_data(dataset: Dataset):
    # We don't just read them from configs.yaml, so that different configs (e.g. 4seasons and 4seasonsCR) can be
    # compared against each other without having the risk that different params are used for the evaluation.

    # groundtruth files are stored in this repository.
    groundtruth_folder = Path('groundtruth_files')
    if dataset == Dataset.euroc:
        folder_names = ['MH_01_easy', 'MH_02_easy', 'MH_03_medium', 'MH_04_difficult', 'MH_05_difficult',
                        'V1_01_easy', 'V1_02_medium', 'V1_03_difficult', 'V2_01_easy', 'V2_02_medium',
                        'V2_03_difficult']
        start_times = [950, 800, 410, 445, 460, 22, 115, 250, 26, 100, 115]
        end_times = [3600, 3000, 2600, 1925, 2200, 2800, 1600, 2020, 2130, 2230, 1880]
        res_prefix = 'mav_'
        folder_names = [res_prefix + folder for folder in folder_names]
        path = groundtruth_folder / 'euroc'
        time_th = 0.8  # Threshold taken over from DSO Matlab evaluation tools.
        # return GroundtruthData and time threshold
        return [GroundtruthDataForSequence(folder_names[i], start_times[i], end_times[i],
                                           path / 'timesFiles' / '{}.txt'.format(folder_names[i]),
                                           path / 'gtFiles' / '{}.txt'.format(folder_names[i])
                                           ) for i in range(len(folder_names))], time_th

    elif dataset == Dataset.tumvi:
        folder_names = ['dataset-corridor1_512_16', 'dataset-corridor2_512_16', 'dataset-corridor3_512_16',
                        'dataset-corridor4_512_16', 'dataset-corridor5_512_16', 'dataset-magistrale1_512_16',
                        'dataset-magistrale2_512_16', 'dataset-magistrale3_512_16', 'dataset-magistrale4_512_16',
                        'dataset-magistrale5_512_16', 'dataset-magistrale6_512_16', 'dataset-outdoors1_512_16',
                        'dataset-outdoors2_512_16', 'dataset-outdoors3_512_16', 'dataset-outdoors4_512_16',
                        'dataset-outdoors5_512_16', 'dataset-outdoors6_512_16', 'dataset-outdoors7_512_16',
                        'dataset-outdoors8_512_16', 'dataset-room1_512_16', 'dataset-room2_512_16',
                        'dataset-room3_512_16', 'dataset-room4_512_16', 'dataset-room5_512_16', 'dataset-room6_512_16',
                        'dataset-slides1_512_16', 'dataset-slides2_512_16', 'dataset-slides3_512_16']
        res_prefix = 'tumvi_'
        folder_names = [res_prefix + folder for folder in folder_names]
        time_th = 0.9  # For TUM-VI we use a larger threshold to ensure that both, the start and the end of the sequence
        # are evaluated
        # return GroundtruthData and time threshold
        path = groundtruth_folder / 'tumvi'
        return [GroundtruthDataForSequence(folder_names[i], 2, None,
                                           path / 'timesFiles' / '{}.txt'.format(folder_names[i]),
                                           path / 'gtFiles' / '{}.txt'.format(folder_names[i])
                                           ) for i in range(len(folder_names))], time_th

    elif dataset == Dataset.four_seasons:
        folder_names = ['office_2021-01-07_12-04-03', 'office_2021-02-25_13-51-57', 'office_2020-03-24_17-36-22',
                        'office_2020-03-24_17-45-31', 'office_2020-04-07_10-20-32', 'office_2020-06-12_10-10-57',
                        'neighbor_2020-10-07_14-47-51', 'neighbor_2020-10-07_14-53-52', 'neighbor_2020-12-22_11-54-24',
                        'neighbor_2021-02-25_13-25-15', 'neighbor_2020-03-26_13-32-55', 'neighbor_2021-05-10_18-02-12',
                        'neighbor_2021-05-10_18-32-32', 'business_2021-01-07_13-12-23', 'business_2021-02-25_14-16-43',
                        'business_2020-10-08_09-30-57', 'country_2020-10-08_09-57-28', 'country_2021-01-07_13-30-07',
                        'country_2020-04-07_11-33-45', 'country_2020-06-12_11-26-43', 'city_2020-12-22_11-33-15',
                        'city_2021-01-07_14-36-17', 'city_2021-02-25_11-09-49', 'oldtown_2020-10-08_11-53-41',
                        'oldtown_2021-01-07_10-49-45', 'oldtown_2021-02-25_12-34-08', 'oldtown_2021-05-10_21-32-00',
                        'parking_2020-12-22_12-04-35', 'parking_2021-02-25_13-39-06', 'parking_2021-05-10_19-15-19']
        res_prefix = '4seasons_'
        folder_names = [res_prefix + folder for folder in folder_names]
        time_th = 0.9
        # return GroundtruthData and time threshold
        path = groundtruth_folder / '4seasons'
        return [GroundtruthDataForSequence(folder_names[i], 2, None,
                                           path / 'timesFiles' / '{}.txt'.format(folder_names[i]),
                                           path / 'gtFiles' / '{}.txt'.format(folder_names[i])
                                           ) for i in range(len(folder_names))], time_th
