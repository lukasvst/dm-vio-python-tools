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

import copy
from trajectory_evaluation.plot_utils import *
from tabulate import tabulate
import matplotlib.pyplot as plt


def square_plot(result: EvalResults):
    """Chooses the right type of square plot based on the dataset.
    For EuRoC rmse until 0.5 is shown (like in the DSO and VI-DSO papers).
    For the other datasets drift until 2 percent is shown.
    """
    dataset = result.dataset
    if dataset == Dataset.euroc:
        # RMSE until 0.5 for EuRoC
        square_plot_base(result, 0.5)
    else:
        # Drift until 2.0 for other datasets.
        square_plot_base(get_normalized_result(result), 2.0)


def square_plot_base(result: EvalResults, vmax=0.5):
    """
    Shows a square_plot where each square represents one execution.
    The rows represent the iterations and the columns the sequences.
    :param result: result to plot.
    :param vmax: Maximum result still showing in the plot (all results worse than this will be shown in red).
    """
    fig = plt.figure()
    errors = result.errors
    errors[errors == np.inf] = 2000  # to show them in plot
    cmap = plt.get_cmap('jet', 100)
    plt.imshow(errors, vmin=0, vmax=vmax, cmap=cmap)
    plt.colorbar()
    plt.title(result.name, loc='left')
    fig.canvas.manager.set_window_title(result.name)
    plt.show()


def results_table(results: List[EvalResults]):
    """Prints a table with the results (automatically choosing the right format for each dataset).
    For EuRoC it will also print the mean rmse, whereas for other datasets it will print mean drift.
    """
    dataset = results[0].dataset
    mean_header = 'mean' if dataset == Dataset.euroc else 'mean drift'
    transpose = dataset != Dataset.euroc
    header = ['result', ''] + get_short_folder_names(results[0].folder_names, dataset) + [mean_header]
    all_data = [header]
    for result in results:
        name = find_between(result.name, '', ':')
        median_errors = result.median_errors.round(3 if dataset == Dataset.euroc else 2).tolist()
        if dataset == Dataset.euroc:
            mean_median_err = result.median_errors.round(3).mean().round(3)
        else:
            mean_median_err = get_normalized_result(result).median_errors.round(2).mean().round(3)
        data = [name, 'rmse'] + median_errors + [mean_median_err]
        all_data.append(data)

        if dataset == Dataset.euroc:
            median_scale_errors = result.median_scale_errors.round(1).tolist()
            mean_median_scale_err = result.median_scale_errors.round(1).mean().round(1)
            scale_data = [name, 'scale_err'] + median_scale_errors + [mean_median_scale_err]
            all_data.append(scale_data)
    if transpose:
        all_data = list(zip(*all_data))

    print(tabulate(all_data, headers='firstrow'))


def line_plot(results: List[EvalResults]):
    """Show a cumulative error plot with all passed results (automatically determining the right settings for the
    dataset:
    For EuRoC rmse until 0.5 is shown (like in the DSO and VI-DSO papers).
    For the other datasets drift until 2 percent is shown.
    """
    dataset = results[0].dataset
    if not all(result.dataset == dataset for result in results):
        raise ValueError("ERROR: Trying to compare runs on different datasets.")
    if dataset == Dataset.euroc:
        line_plot_base(results, 0.5)
    elif dataset == Dataset.tumvi or dataset == Dataset.four_seasons:
        line_plot_base(get_normalized_results(results), 2.0)


def line_plot_base(results: List[EvalResults], threshold=2.0):
    """
    Show a cumulative error plot.
    :param results: results to show.
    :param threshold: maximum result still shown in the plot.
    """
    sorted_errors_all = get_sorted_errors(results)
    plt.figure()
    for i, sorted_errors in enumerate(sorted_errors_all):
        sorted_errors[sorted_errors == np.inf] = 2000  # to show them in plot
        plt.plot(sorted_errors, np.arange(sorted_errors.size), label=results[i].name)
    plt.axis([0, threshold, 0, len(sorted_errors)])
    plt.grid(True)
    plt.legend(loc='lower left')
    plt.show()


def get_normalized_results(results):
    """Return copy of results normalized by trajectory length (drift in percentage)."""
    return [get_normalized_result(result) for result in results]


def get_normalized_result(result: EvalResults):
    """Return copy of results normalized by trajectory length (drift in percentage)."""
    normalizer = get_normalizer(result)
    ret = copy.deepcopy(result)
    ret.errors = ret.errors / normalizer
    ret.median_errors = ret.median_errors / normalizer
    return ret
