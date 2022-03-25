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

from trajectory_evaluation.evaluate import EvalResults, Dataset
import numpy as np
from typing import List


def get_sorted_errors(results: List[EvalResults]):
    # First make sure that all results have the same number of iteration.
    num_iters = [result.num_iter for result in results]
    min_iter = min(num_iters)
    if min_iter != max(num_iters):
        print(
            'WARNING: Not all evaluated results have the same number of iterations. Only using the first {} runs for '
            'each result'.format(
                min_iter))
    errors = [result.errors[0:min_iter, :] for result in results]
    sorted_errors = [np.sort(error.flatten()) for error in errors]
    return sorted_errors


def find_between(string, begin, end):
    return string[string.find(begin) + len(begin):string.rfind(end)]


def get_short_folder_names(folder_names: List[str], dataset):
    if dataset == Dataset.euroc:
        return [name[4:9] for name in folder_names]
    elif dataset == Dataset.tumvi:
        return [find_between(name, 'tumvi_dataset-', '_512_16') for name in folder_names]
    elif dataset == Dataset.four_seasons:
        return [find_between(name, '4seasons_', '') for name in folder_names]
    else:
        return folder_names


def get_normalizer(result):
    """Return array to convert results to drift in percent."""
    dataset = result.dataset
    if dataset == Dataset.tumvi:
        trajectory_lengths = [305, 322, 300, 114, 270, 918, 561, 566, 688, 458, 771, 2656, 1601, 1531, 928, 1168, 2045,
                              1748, 986, 146, 142, 135, 68, 131, 67, 289, 299, 383]
    elif dataset == Dataset.four_seasons:
        map = dict()
        map['4seasons_business_2020-10-08_09-30-57'] = 3011.6408305623318
        map['4seasons_business_2021-01-07_13-12-23'] = 3240.980487664213
        map['4seasons_business_2021-02-25_14-16-43'] = 3251.9095169019683
        map['4seasons_city_2020-12-22_11-33-15'] = 10780.574894006673
        map['4seasons_city_2021-01-07_14-36-17'] = 10527.071542250924
        map['4seasons_city_2021-02-25_11-09-49'] = 10640.53519930362
        map['4seasons_country_2020-04-07_11-33-45'] = 6580.585081043755
        map['4seasons_country_2020-06-12_11-26-43'] = 6573.179452595141
        map['4seasons_country_2020-10-08_09-57-28'] = 6555.597982195476
        map['4seasons_country_2021-01-07_13-30-07'] = 6537.982081484175
        map['4seasons_neighbor_2020-03-26_13-32-55'] = 2106.0377819934765
        map['4seasons_neighbor_2020-10-07_14-47-51'] = 2120.4493722818506
        map['4seasons_neighbor_2020-10-07_14-53-52'] = 2124.5717222968324
        map['4seasons_neighbor_2020-12-22_11-54-24'] = 2153.5269533455735
        map['4seasons_neighbor_2021-02-25_13-25-15'] = 1885.7081876201207
        map['4seasons_neighbor_2021-05-10_18-02-12'] = 2160.656632453823
        map['4seasons_neighbor_2021-05-10_18-32-32'] = 2166.919763495766
        map['4seasons_office_2020-03-24_17-36-22'] = 3775.4838890943192
        map['4seasons_office_2020-03-24_17-45-31'] = 3776.5684518918497
        map['4seasons_office_2020-04-07_10-20-32'] = 3790.7053757221142
        map['4seasons_office_2020-06-12_10-10-57'] = 3776.8626523979783
        map['4seasons_office_2021-01-07_12-04-03'] = 3790.960147973857
        map['4seasons_office_2021-02-25_13-51-57'] = 3772.201462140006
        map['4seasons_oldtown_2020-10-08_11-53-41'] = 5034.444436444601
        map['4seasons_oldtown_2021-01-07_10-49-45'] = 5060.695199977825
        map['4seasons_oldtown_2021-02-25_12-34-08'] = 5110.7036112953065
        map['4seasons_oldtown_2021-05-10_21-32-00'] = 5134.989596529747
        map['4seasons_parking_2020-12-22_12-04-35'] = 1000.7504517487432
        map['4seasons_parking_2021-02-25_13-39-06'] = 846.1020208454354
        map['4seasons_parking_2021-05-10_19-15-19'] = 757.6168617773346
        trajectory_lengths = [map[name] for name in result.folder_names]
    else:
        raise ValueError("Unsupported dataset for normalization.")

    return np.array(trajectory_lengths) / 100.0
