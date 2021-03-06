from trajectory_evaluation.evaluate import evaluate_run, Dataset
from pathlib import Path
from trajectory_evaluation.plots import square_plot, results_table, line_plot

# Insert path to the downloaded results here.
folder = '/path/to/dm-vio_paper_results/results'

# ============================== Results definitions autogenerated ==============================

# ORB-SLAM3 mono-inertial result.
resorb0_tumvi_home, gtscale_orb0_tumvi_home = evaluate_run(Path(folder) / 'orbresult-tumvi-2021-08-22--19-37-15', Dataset.tumvi, 5, 'orb0_tumvi_home ORB-SLAM3 mono-inertial result.: output=save ')

# ORB-SLAM3 stereo-inertial result.
resorb1_4seasonsCR_home, gtscale_orb1_4seasonsCR_home = evaluate_run(Path(folder) / 'orbresult-4seasonsCR-2021-08-17--20-05-21', Dataset.four_seasons, 5, 'orb1_4seasonsCR_home ORB-SLAM3 stereo-inertial result.: output=save ')
# ORB-SLAM3 mono-inertial result.
resorb2_4seasonsCR_home, gtscale_orb2_4seasonsCR_home = evaluate_run(Path(folder) / 'orbresult-4seasonsCR-2021-08-19--01-59-28', Dataset.four_seasons, 5, 'orb2_4seasonsCR_home ORB-SLAM3 mono-inertial result.: output=save ')

# Main paper result. settings=tumvi.yaml maxPreloadImages=16000
res3_RT_tumvi_mac, gtscale_3_RT_tumvi_mac = evaluate_run(Path(folder) / 'dmvioresult-tumvi-RT-2021-08-28--18-44-35', Dataset.tumvi, 5, '3_RT_tumvi_mac Main paper result.: output=null_quiet settings=tumvi.yaml maxPreloadImages=16000 ')
# Main paper result. settings=euroc.yaml
res4_RT_euroc_mac, gtscale_4_RT_euroc_mac = evaluate_run(Path(folder) / 'dmvioresult-euroc-RT-2021-08-29--23-34-45', Dataset.euroc, 10, '4_RT_euroc_mac Main paper result.: output=null_quiet settings=euroc.yaml ')
# Main paper result. settings=4seasons.yaml maxPreloadImages=16000
res5_RT_4seasonsCR_mac, gtscale_5_RT_4seasonsCR_mac = evaluate_run(Path(folder) / 'dmvioresult-4seasonsCR-RT-2021-08-30--04-05-35', Dataset.four_seasons, 5, '5_RT_4seasonsCR_mac Main paper result.: output=null_quiet settings=4seasons.yaml maxPreloadImages=16000 ')
# Ablation no dynamic weights. settings=tumvi.yaml maxPreloadImages=16000 dynamicWeightRMSEThresh=1e6
res6_RT_tumvi_mac, gtscale_6_RT_tumvi_mac = evaluate_run(Path(folder) / 'dmvioresult-tumvi-RT-2021-11-09--15-37-00', Dataset.tumvi, 5, '6_RT_tumvi_mac Ablation no dynamic weights.: output=null_quiet settings=tumvi.yaml maxPreloadImages=16000 dynamicWeightRMSEThresh=1e6 ')

# VI-DSO results. maxPreloadImages=16000
res7_RT_tumvi_mac, gtscale_7_RT_tumvi_mac = evaluate_run(Path(folder) / 'dsoresult-tumvi-RT-2021-08-31--13-42-15', Dataset.tumvi, 5, '7_RT_tumvi_mac VI-DSO results.: output=null_quiet maxPreloadImages=16000 ')

# VI-DSO results. maxPreloadImages=16000 accelerometer_noise_density=0.10200528 gyroscope_noise_density=4.120916e-02 accelerometer_random_walk=9.8082e-04 gyroscope_random_walk=3.8785e-04 setting_weightZeroPriorDSOInitY=5e09 setting_weightZeroPriorDSOInitX=5e09
res8_RT_4seasonsCR_mac, gtscale_8_RT_4seasonsCR_mac = evaluate_run(Path(folder) / 'dsoresult-4seasonsCR-RT-2021-09-01--11-51-42', Dataset.four_seasons, 5, '8_RT_4seasonsCR_mac VI-DSO results.: output=null_quiet maxPreloadImages=16000 accelerometer_noise_density=0.10200528 gyroscope_noise_density=4.120916e-02 accelerometer_random_walk=9.8082e-04 gyroscope_random_walk=3.8785e-04 setting_weightZeroPriorDSOInitY=5e09 setting_weightZeroPriorDSOInitX=5e09 ')

# Basalt stereo-inertial results. config=tumvi_512_config.json calib=4seasons_calibInfl1000.json
resbasalt9_4seasonsCR_mac, gtscale_basalt9_4seasonsCR_mac = evaluate_run(Path(folder) / 'basaltresult-4seasonsCR-2021-09-07--20-33-36', Dataset.four_seasons, 5, 'basalt9_4seasonsCR_mac Basalt stereo-inertial results.: output=save config=tumvi_512_config.json calib=4seasons_calibInfl1000.json ')

# DM-VIO Non-RT result for ablation. settings=4seasons.yaml
res10_4seasons_slurm, gtscale_10_4seasons_slurm = evaluate_run(Path(folder) / 'dmvioresult-4seasons-2021-11-03--14-45-21', Dataset.four_seasons, 5, '10_4seasons_slurm DM-VIO Non-RT result for ablation.: output=null_quiet settings=4seasons.yaml ')
# Ablation no reinit and no marg replacement. settings=4seasons.yaml init_transitionModel=1 init_ba_reinitScaleUncertaintyThresh=1e6
res11_4seasons_slurm, gtscale_11_4seasons_slurm = evaluate_run(Path(folder) / 'dmvioresult-4seasons-2021-11-03--14-45-52', Dataset.four_seasons, 5, '11_4seasons_slurm Ablation no reinit and no marg replacement.: output=null_quiet settings=4seasons.yaml init_transitionModel=1 init_ba_reinitScaleUncertaintyThresh=1e6 ')
# Ablation no initial readvancing. settings=4seasons.yaml init_transitionModel=4 init_ba_reinitScaleUncertaintyThresh=1e6 init_scalePriorAfterInit=1.0
res12_4seasons_slurm, gtscale_12_4seasons_slurm = evaluate_run(Path(folder) / 'dmvioresult-4seasons-2021-11-03--14-46-13', Dataset.four_seasons, 5, '12_4seasons_slurm Ablation no initial readvancing.: output=null_quiet settings=4seasons.yaml init_transitionModel=4 init_ba_reinitScaleUncertaintyThresh=1e6 init_scalePriorAfterInit=1.0 ')
# Ablation no PGBA. settings=4seasons.yaml init_transitionModel=5 init_scalePriorAfterInit=1.0
res13_4seasons_slurm, gtscale_13_4seasons_slurm = evaluate_run(Path(folder) / 'dmvioresult-4seasons-2021-11-03--14-46-25', Dataset.four_seasons, 5, '13_4seasons_slurm Ablation no PGBA.: output=null_quiet settings=4seasons.yaml init_transitionModel=5 init_scalePriorAfterInit=1.0 ')

# ============================== Plotting code ==============================
# -------------------- EuRoC Table (Table 1) --------------------
results_table([res4_RT_euroc_mac])

# square plot showing all executions (not in the paper).
square_plot(res4_RT_euroc_mac)

# -------------------- TUM-VI Table (Table 2) --------------------
results_table([res3_RT_tumvi_mac])

# -------------------- TUM-VI plot (Fig. 4) --------------------
line_plot([res3_RT_tumvi_mac, resorb0_tumvi_home, res7_RT_tumvi_mac])

# -------------------- 4Seasons plot (Fig. 5) --------------------
line_plot([res5_RT_4seasonsCR_mac, resorb2_4seasonsCR_home, resorb1_4seasonsCR_home, resbasalt9_4seasonsCR_mac,
           res8_RT_4seasonsCR_mac])

# -------------------- Method ablation plot (Fig. S1) --------------------
line_plot([res10_4seasons_slurm, res11_4seasons_slurm, res12_4seasons_slurm, res13_4seasons_slurm])

# -------------------- Weights ablation (Fig. S2)
line_plot([res3_RT_tumvi_mac, res6_RT_tumvi_mac])
# last 3 columns correspond to the slides sequences shown in Fig. S2b and c.
square_plot(res3_RT_tumvi_mac)
square_plot(res6_RT_tumvi_mac)

# Note: The original plots for the paper were generated using Matlab, hence the colors / style is slightly different.
