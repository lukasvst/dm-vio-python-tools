import argparse
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from enum import Enum
from utils.config_utils import read_config, input_custom_variables
from utils.save_setup import save_setup
from utils.slurm_utils import execute_commands_slurm


class OutputType(Enum):
    save = 0
    console = 1
    null = 2


class BuildType(Enum):
    Debug = 0
    RelWithDebInfo = 1
    Release = 2


class RunCommand:
    """Data for a command which should be run."""

    def __init__(self, command, working_dir, post_run_commands):
        """
        :param command: The main command which shall be run (DM-VIO execution).
        :param working_dir: The working directory to run it in.
        :param post_run_commands: Commands which should be run afterwards (e.g. moving the results to the correct
        places).
        """
        self.command = command
        self.working_dir = working_dir
        self.post_run_commands = post_run_commands


def main():
    # Read parameters (name, selected config, custom dmvio params.)
    parser = argparse.ArgumentParser(description='Run DM-VIO.')
    parser.add_argument('--name', type=str, default="dmvioresult",
                        help="Name of the result (optional, but can be useful to identify the result later.")
    parser.add_argument('--config', type=str, default=None,
                        help="Config to use. If not set it will use the one in defaultconfig.txt")
    parser.add_argument('--build_type', type=str, default='RelWithDebInfo', help="Build type to compile with.")
    parser.add_argument('--dataset', type=str, default='euroc', help='Dataset to run on.')
    parser.add_argument('--iter', default=None, type=int, help='Number of iterations to use.')
    parser.add_argument('--only_seq', default=None, type=int, help='Only run one sequence.')
    parser.add_argument('--realtime', action='store_true', help='Run in realtime mode.')
    parser.add_argument('--pull', default=False, action='store_true', help='Git pull before running.')
    parser.add_argument('--dmvio_args', type=str, default=None, help='Additional commandline arguments for DM-VIO.')
    parser.add_argument('--dmvio_settings', type=str, default=None,
                        help='Settings file to use (path is relative to DM-VIO-Source-Folder/configs)')
    parser.add_argument('--withgui', default=False, action='store_true', help='Enable GUI in DM-VIO.')
    parser.add_argument('--noimu', default=False, action='store_true', help='Turn off IMU.')
    parser.add_argument('--output', type=str, default='save',
                        help="What to do with console output, either 'save', 'null' (to delete) or console. For Slurm "
                             "console doesn't work as intended, as the output is routed to a log file anyway.")
    parser.add_argument('--quiet', default=False, action='store_true',
                        help='Set quiet=1 for DM-VIO execution (disables some of the output).')
    parser.add_argument('--temporary', default=False, action='store_true',
                        help='If True the name will not be enhanced with a date, and an already existing results '
                             'folder will be overwritten (to be specific first deleted, written newly).')
    parser.add_argument('--dryrun', default=False, action='store_true', help='Dont actually run.')
    parser.add_argument('--mail_type', default='NONE', type=str,
                        help='Only for Slurm: which mails to send (e.g ALL or NONE).')
    parser.add_argument('--num_tasks', type=str, default=None, help='Num tasks to report to slurm.')
    parser.add_argument('--num_nodes', type=str, default=None, help='Num nodes to report to slurm.')
    parser.add_argument('--gdb', default=False, action='store_true',
                        help='Debug with gdb and stop as soon as error happens.')
    args = parser.parse_args()

    # Read config.
    config, config_name, general_config, _ = read_config(args.config)
    if config is None:
        print('Error: config has to specified.')
        sys.exit(1)

    realtime = args.realtime
    noimu = args.noimu
    dataset = args.dataset

    name = args.name
    results_name, time_used_for_name = build_results_name(name, realtime, dataset)
    temporary = args.temporary
    if temporary:
        results_name = name + '-' + dataset

    build_type = BuildType[args.build_type]

    # Folders.
    dmvio_folder = config['dmvio_folder']

    build_folder_name = 'cmake-build-{}'.format(build_type.name.lower())
    build_folder = Path(dmvio_folder) / build_folder_name
    if not build_folder.exists():
        build_folder.mkdir()
    dmvio_executable = build_folder / 'bin' / 'dmvio_dataset'

    dataset_config = general_config[dataset]
    try:
        dataset_config.update(config[dataset])
    except KeyError as e:
        print(
            "Error: Dataset not in key. Have you downloaded the dataset already and inserted the key into your config?")
        raise e
    general_save_folder = dataset_config['results_path']
    results_folder = Path(general_save_folder) / results_name

    # General variables
    use_slurm = config['slurm']
    output_type = OutputType[args.output]
    if output_type == OutputType.console:
        assert use_slurm is False, 'Output type console should not be used with Slurm.'
    quiet = args.quiet
    if output_type == OutputType.null:
        # Always use quiet if the output isn't saved anyway.
        quiet = True

    num_iter = args.iter
    if num_iter is None:
        num_iter = dataset_config['default_iter']
    print('Num iterations: {}'.format(num_iter))
    only_seq = args.only_seq

    # Maybe Git pull code
    if args.pull:
        git_pull(dmvio_folder)

    # Build code
    build_code(build_folder, build_type, config['cmake_command'] if 'cmake_command' in config else None)

    # Create save folder
    if not results_folder.exists():
        results_folder.mkdir()
    else:
        print('WARNING: Results folder already exists.')
        if temporary:
            subprocess.run('rm -r {}'.format(results_folder), shell=True)
            results_folder.mkdir()
        else:
            sys.exit(1)

    # -> Create array of commands and working directories
    # -> For a normal script we can just run them one by one, for Slurm we need to write them to an sbatch file which
    # is then run.
    settings_file = args.dmvio_settings
    if not settings_file is None:
        settings_file = str(Path(dmvio_folder) / 'configs' / settings_file)

    commands = create_dmvio_commands(dmvio_executable, dmvio_folder, dataset_config, results_folder, num_iter,
                                     only_seq, output_type,
                                     realtime, args.withgui, noimu, quiet, args.dmvio_args, settings_file, args.gdb)

    # ------------------------------ Save Project Status ------------------------------
    setup = {
        'name': name,
        'dataset': dataset,
        'build_type': build_type.name,
        'num_iter': num_iter,
        'only_seq': only_seq,
        'results_name': results_name,
        'config_name': config_name,
        'date_run': time_used_for_name,
        'realtime': realtime,
        'temporary': temporary,
        'noimu': noimu,
        'quiet': quiet,
        'output_type': output_type.name,
        'withgui': args.withgui,
        'custom_dmvio_args': '' if args.dmvio_args is None else args.dmvio_args,
        'dmvio_settings': '' if args.dmvio_settings is None else args.dmvio_settings,
        'gdb': args.gdb
    }
    # in this folder we save all details about environment, code versions, etc.
    setup_folder = results_folder / 'setup'
    setup_folder.mkdir()
    save_setup(setup, setup_folder, dmvio_folder, config, commands)

    # ------------------------------ Run-Loop -> Run / create Slurm script. ------------------------------
    print("----------- STARTING EXECUTION! -----------")
    if not use_slurm:
        execute_commands(commands, args.dryrun, setup_folder)

        # Transfer results to Uni (if not there already).
        if 'rsync_command' in config and not temporary:
            rsync_command = config['rsync_command']
            rsync_target = config['rsync_command_target']
            full_rsync_command = '{} {} {}/'.format(rsync_command, results_folder, rsync_target)
            print(full_rsync_command)
            subprocess.run(full_rsync_command, shell=True)
    else:
        execute_commands_slurm(commands, setup_folder, dataset_config['slurm_mem'], dataset_config['slurm_time'],
                               args.mail_type, args.num_tasks, args.num_nodes)


def execute_commands(commands, dryrun, setup_folder):
    for command in commands:
        print('Working Dir: {}'.format(command.working_dir))
        print('Command: {}'.format(command.command))
        if not dryrun:
            subprocess.run(command.command, shell=True, cwd=command.working_dir)
            for move_command in command.post_run_commands:
                print('Executing: {}'.format(move_command))
                subprocess.run(move_command, shell=True)
    subprocess.run('echo Finished > {}'.format(setup_folder / 'Finished.txt'), shell=True)


def create_dmvio_commands(dmvio_executable, dmvio_folder, dataset_config, results_folder, num_iter, only_seq,
                          output_type, realtime,
                          withgui, noimu, quiet, custom_dmvio_args, dmvio_settings_file, gdb):
    # ------------------------------ Create DSO Commands: ------------------------------
    # - Argument-specific parts: nogui, preset (realtime or not) -> Set here (passed arguments).
    # - Dataset-specific parts: camera-folder-name, (imu, camera and photometric) calibration-name, mode (with
    # photometric calibration or not) -> Set in config -> dataset_arguments
    # - Sequence-specific parts: Start and end-time -> set with array in config, output-path -> set here.
    nogui_arg = 0 if withgui else 1
    preset_arg = 1 if realtime else 0
    imu_arg = 0 if noimu else 1
    quiet_arg = 1 if quiet else 0
    settings_arg = ''
    if not dmvio_settings_file is None:
        settings_arg = ' settingsFile=' + dmvio_settings_file
    dmvio_general_arguments = 'preset={} nogui={} useimu={} quiet={}{}'.format(preset_arg, nogui_arg, imu_arg,
                                                                               quiet_arg, settings_arg)
    dataset_arguments = input_custom_variables(dataset_config['dataset_args'], dmvio_folder)
    dmvio_arguments = '{} {}'.format(dataset_arguments, dmvio_general_arguments)
    if not custom_dmvio_args is None:
        dmvio_arguments += ' ' + custom_dmvio_args
    print(dmvio_arguments)

    start_times = None
    end_times = None
    if 'start_times' in dataset_config:
        start_times = dataset_config['start_times']
    else:
        print('WARNING: No start times for dataset.')
    if 'end_times' in dataset_config:
        end_times = dataset_config['end_times']
    else:
        print('WARNING: No end times for dataset.')

    folders = dataset_config['folder_names']
    dataset_path = Path(dataset_config['dataset_path'])
    afterpath = dataset_config['afterpath']
    res_prefix = dataset_config['res_prefix']

    commands = []
    for i, folder in enumerate(folders):
        if not only_seq is None and i != only_seq:
            continue
        for iter in range(num_iter):
            working_directory = dataset_path / folder / afterpath
            run_name = '{}{}_{}'.format(res_prefix, folder, iter)
            results_folder_sequence = results_folder / run_name
            results_folder_sequence.mkdir()
            # Note the trailing slash which is important to have it saved in the folder (otherwise it's a prefix to
            # the filename).
            full_arguments = '{} resultsPrefix={}/'.format(dmvio_arguments,
                                                           results_folder_sequence)
            if not start_times is None:
                full_arguments += ' start=' + str(start_times[i])
            if not end_times is None:
                full_arguments += ' end=' + str(end_times[i])

            pipestring = ''
            if output_type == OutputType.null:
                pipestring = ' > /dev/null'
            elif output_type == OutputType.save:
                runoutput_folder = results_folder / 'runoutputs'
                runoutput_filename = '{}_runoutput.txt'.format(run_name)
                if not runoutput_folder.exists():
                    runoutput_folder.mkdir()
                pipestring = ' > {} 2>&1'.format(runoutput_folder / runoutput_filename)

            command = "{} {}{}".format(dmvio_executable, full_arguments, pipestring)
            if gdb:
                command = "gdb -ex='set confirm on' -ex=run -ex=quit --args {} {}".format(dmvio_executable,
                                                                                          full_arguments)

            move_commands = []
            traj_results_folder = results_folder / 'results'
            if not traj_results_folder.exists():
                traj_results_folder.mkdir()
            kf_results_folder = results_folder / 'kfres'
            if not kf_results_folder.exists():
                kf_results_folder.mkdir()
            move_commands.append('cp {} {}'.format(results_folder_sequence / 'result.txt',
                                                   traj_results_folder / '{}.txt'.format(run_name)))
            move_commands.append('cp {} {}'.format(results_folder_sequence / 'resultKFs.txt',
                                                   kf_results_folder / '{}.txt'.format(run_name)))
            commands.append(RunCommand(command, working_directory, move_commands))
    return commands


def build_code(build_folder, build_type, cmake_command=None):
    # Using the same cmake command as Clion to make sure to not build twice unnecessarily.
    if cmake_command is None:
        cmake_command = 'cmake'
    result_cmake = subprocess.run('{} -DCMAKE_BUILD_TYPE={} ..'.format(cmake_command, build_type.name), shell=True,
                                  cwd=build_folder)
    if result_cmake.returncode != 0:
        print("CMake failed!")
        sys.exit(1)
    result = subprocess.run('make -j8', shell=True, cwd=build_folder)
    if result.returncode != 0:
        print("Compilation failed!")
        sys.exit(1)


def git_pull(dmvio_folder):
    print('Running Git pull from DM-VIO directory.')
    returned = subprocess.run('git pull', shell=True, cwd=dmvio_folder)
    if returned.returncode != 0:
        print('Git pull failed.')
        sys.exit(1)


def build_results_name(name, realtime, dataset):
    # Build results name
    # -> What to use?:
    # General: RT or not, machine run on, build type. Git diff empty or not.
    # Time, Git commit (log or hash).
    time = datetime.today()
    timestr = time.strftime('%Y-%m-%d--%H-%M-%S')
    results_name = name + '-'
    if not dataset is None:
        results_name += dataset + '-'
    if realtime:
        results_name += 'RT-'
    results_name += timestr
    print('Results-name: ', results_name)
    return results_name, time


if __name__ == "__main__":
    main()
