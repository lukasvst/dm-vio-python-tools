# Python tools for DM-VIO: Delayed Marginalization Visual-Inertial Odometry

When using this project in academic work, please consider citing:

    @article{stumberg22dmvio,
      author = {L. von Stumberg and D. Cremers},
      title = {{DM-VIO}: Delayed Marginalization Visual-Inertial Odometry},
      journal = {{IEEE} Robotics and Automation Letters ({RA-L})},
      year = {2022},
      volume = {7},
      number = {2},
      pages = {1408-1415},
      doi = {10.1109/LRA.2021.3140129}
    }

### Dependencies:

Install dependencies with:

        pip3 install tqdm ruamel.yaml pyquaternion matplotlib tabulate

### Step 0: Download and build DM-VIO

Go to https://github.com/lukasvst/dm-vio.git and follow the build instructions.

### Step 1: Create config

For each machine you want to run DM-VIO on, you first need to create a configuration inside `configs.yaml`. The script
`create_config.py` does this for you:

    git clone https://github.com/lukasvst/dm-vio-python-tools.git
    cd dm-vio-python-tools
    python3 create_config.py --name=workpc --dmvio_folder=/path/to/dmvio --results_folder=/results/will/be/saved/here

### Step 2: Download and Prepare datasets

Run any of the following commands to download and prepare the respective dataset:

    python3 download_euroc.py --folder=/dataset/shall/be/saved/here/euroc
    python3 download_tumvi.py --folder=/dataset/shall/be/saved/here/tumvi
    python3 download_4seasons.py --folder=/dataset/shall/be/saved/here/4seasons

    # Useful For testing: use --only_seq to only download the first sequence
    python3 download_euroc.py --folder=/dataset/shall/be/saved/here/euroc --only_seq=0 

For EuRoC and 4Seasons you should still run the above command even if you have already downloaded the dataset, because
they perform necessary preparations (interpolating IMU data, etc.) for DM-VIO to run on the respective dataset. The
scripts will skip downloading existing folders, so you can pass the existing location of the dataset.

### Step 3: Run DM-VIO on datasets

These commands are good to start with (only run one sequence each, with GUI, etc.)

    python3 run_dmvio.py --output=console --dataset=euroc --dmvio_settings=euroc.yaml --withgui --iter=1 --only_seq=10
    python3 run_dmvio.py --output=console --dataset=tumvi --dmvio_settings=tumvi.yaml --withgui --iter=1 --only_seq=25
    python3 run_dmvio.py --output=console --dataset=4seasons --dmvio_settings=4seasons.yaml --withgui --iter=1 --only_seq=0

`--only_seq` makes it run on only one sequence (e.g. V2_03 / slides1 in the examples above)

`--iter=1` makes it run on each sequence only once (where the default is 10 times on EuRoC and 5 times on TUM-VI /
4Seasons)

When you leave these settings out, it will perform a full evaluation on the dataset, keep in mind that this will take a
lot of time.
[Here you can find the commands for generating all paper results.](doc/CommandsForPaperResults.md)

The script `run_dmvio.py` will not only run DM-VIO but it will also save useful information (like the used version of
the code, versions of installed libraries, etc.) to `setup/setup.yaml`. This makes sure that results cannot get mixed up
and helps reproducability.

#### Interesting commandline arguments

To show all arguments just run

    python3 run_dmvio.py --help

Most important arguments are

* `dataset`: To specify which dataset to evaluate one.
* `dmvio_settings`: The settings file (located relative to the config folder in the DM-VIO source code), which can
  specify multiple parameters (and IMU noise values).
* `dmvio_args`: Additional commandline arguments passed to DM-VIO. These will also override settings potentially set in
  the settings file passed with `dmvio_settings`.

### Step 4: Create Python evaluation evaluation file

Evaluating your results is a two-step process. First a python evaluation file is created:

    python3 create_python_evaluation_file.py

This will generate a new file `evaluations.py` (in the main folder of this project) which contains commands to compute
the absolute trajectory error for each result on your machine. Each line looks similar to this:

    # Main paper result. settings=tumvi.yaml maxPreloadImages=16000
    res3_RT_tumvi_mac, gtscale_3_RT_tumvi_mac = evaluate_run(Path(folder) / 'dmvioresult-tumvi-RT-2021-08-28--18-44-35', Dataset.tumvi, 5, '3_RT_tumvi_mac Main paper result.: output=null_quiet settings=tumvi.yaml maxPreloadImages=16000 ')

After executing this line (e.g. in a Jupyter notebook), `res3_RT_tumvi_mac` will contain the evaluation results when
using the estimated scale, and `gtscale_3_RT_tumvi_mac` will contain the results when using the groundtruth scale. In
practice you should almost always use the former `res*`, unless the method cannot observe the metric scale (like when
passing `--noimu`).

The comment line above each result shows the commit message of the version of the code used for this run, as well as the
used settings and if there were local changes to the code (indicated by `+DIFF`). The result name provides some
information about the run, like which machine it was run on, which commit of the code was used, if it was
realtime (`RT`), if only a part of the dataset was evaluated on (`_part`), etc.

You can use the following tools to analyse the results:

#### Create a plot where each execution is represented by a colored square (useful to get a quick overview over a result)

    square_plot(res3_RT_tumvi_mac)

#### Cumulative error plot. This should be the main tool for comparing results as it summarizes all executions in a meaningful way

    line_plot([res3_RT_tumvi_mac, res6_RT_tumvi_mac])

#### Results table. Print the median error for each sequence and the mean median rmse (euroc) / mean median drift (TUM-VI)

    results_table([res3_RT_tumvi_mac, res6_RT_tumvi_mac])

As an example how to use these commands, you can look at the script `paper_evaluations.py`, which generates the plots 
shown in the paper. In the script you need to set the folder to the 
[paper results, which you can download here](https://vision.in.tum.de/webshare/g/dm-vio/dm-vio_paper_results.zip).

Hint: For using these tools in practice, I recommend to either

* open an interactive python console, run `from evaluations import *` in it and then run any of the plots above.
* use a Jupyter notebook or normal python script to perform more complex analysis. For this you should copy individual
  lines from `evaluations.py`
  over to the Jupyter notebook (rather than importing the `evaluations.py`), to make sure that the names don't change
  when new results are added and `evaluations.py` is regenerated.

You can also modify `create_python_evaluation_file.py` to filter results or sort them differently.


### Using multiple machines for running (and how to use configs.yaml)

These evaluation tools are designed with multiple machines for evaluations in mind. The idea is that for each machine
one configuration inside `configs.yaml` is created [see above](#step-1-create-config). The `configs.yaml` file can be
shared across machines with Git (by forking this repository). The only local-only file is `defaultconfig.txt` which
should not be put into Git and defines which configuration should be used for each machine.

#### Syncing results to central machine (e.g. a server)

The tools support

* automatic uploading of results to a central machine after `run_dmvio.py` has finished.
* automatic downloading of results from the central machine at the beginning of `create_evaluation_file.py`. For this,
  just use set following fields of your configuration in `configs.yaml`, e.g.:

      rsync_command: rsync -rav -e "ssh -p YOUR_SSH_PORT"
      rsync_command_target: user@your.central.machine:/folder/to/save/results/on/central/machine

When setting this up properly you can use `run_dmvio.py` on any of your machines, and afterwards
run `create_python_evaluation_file.py`
on your home machine to gather all results.

### License

This repository is published under the BSD 3-Clause License. The files trajectory_evaluation/associate.py and
trajectory_evaluation/evaluate.py are based on the TUM-RGBD tools written by Juergen Sturm. Some changes to it like the
Sim(3) alignment are inspired by the dso-Matlab-evaluation tools written by Jakob Engel. The times and groundtruth files
for EuRoC are taken from the supplementary material for DSO. The other code was written by Lukas von Stumberg at TUM.
