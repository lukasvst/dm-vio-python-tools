### Commands for obtaining the paper results

#### Download paper results for comparison:

You can download the paper results at: https://vision.in.tum.de/webshare/g/dm-vio/dm-vio_paper_results.zip

The plots and tables from the paper can be reproduced using the script `paper_evaluations.py`.
For this you need to insert the path to the downloaded results at the beginning of the script.

#### Non-realtime results

These are not shown in the paper, but as they do not depend as much on the individual machine it makes sense to run them
first.

    python3 run_dmvio.py --output=null --dataset=euroc --dmvio_settings=euroc.yaml
    python3 run_dmvio.py --output=null --dataset=tumvi --dmvio_settings=tumvi.yaml
    python3 run_dmvio.py --output=null --dataset=4seasons --dmvio_settings=4seasons.yaml

#### Realtime paper results

    python3 run_dmvio.py --output=null --dataset=euroc --dmvio_settings=euroc.yaml --realtime --dmvio_args="maxPreloadImages=16000"
    python3 run_dmvio.py --output=null --dataset=tumvi --dmvio_settings=tumvi.yaml --realtime --dmvio_args="maxPreloadImages=16000"
    python3 run_dmvio.py --output=null --dataset=4seasons --dmvio_settings=4seasons.yaml --realtime --dmvio_args="maxPreloadImages=16000"

##### Notes:
* adjust `maxPreloadImages` according to the RAM available on your machine, these values were meant to be used with
  16GB. With enough RAM (>=32GB) you should not need this argument at all.
* for 4Seasons `--dataset=4seasonsCR` was used for the main paper results to make absolutely sure it uses exactly the
  same images as the other evaluated methods. But `--datset=4seasons` should be mostly the same and doesn't need the
  long dataset preprocessing (which can be performed by passing `--crop_images` to `download_4seasons.py`).

#### Method ablation (Fig. S1)

These should not be run in realtime mode as some of the ablations are not designed for it.

    # Normal method
    python3 run_dmvio.py --output=null --dataset=4seasons --dmvio_settings=4seasons.yaml
    # 1. No Reinit and no Marginalization Replacement
    python3 run_dmvio.py --output=null --dataset=4seasons --dmvio_settings=ablations/4seasonsNoReinitAndMargReplacement.yaml
    # 2. No Initial Readvancing (+ all changes in 1.)
    python3 run_dmvio.py --output=null --dataset=4seasons --dmvio_settings=ablations/4seasonsNoInitialReadvancing.yaml
    # 3. No PGBA (+ all changes in 2.)
    python3 run_dmvio.py --output=null --dataset=4seasons --dmvio_settings=ablations/4seasonsNoPGBA.yaml

Note that after the paper publication the parameter `setting_minFramesBetweenKeyframes` has been added, which slightly
improves the non-realtime results and brings them closer to the realtime results. You can also reproduce the original
paper ablation by adding `--dmvio_args="setting_minFramesBetweenKeyframes=0"` to all the lines above.

#### Weight ablation (Fig. S2)

    # Disable dynamic weight
    python3 run_dmvio.py --output=null --dataset=tumvi --dmvio_settings=tumvi.yaml --realtime --dmvio_args="maxPreloadImages=16000 dynamicWeightRMSEThresh=1e6"

#### Notes on reproducing the results:

Like DSO, DM-VIO is nondeterministic, which is why we run multiple times on each sequence. Therefore it is best to
inspect the cumulative error plots (`line_plot`), rather than looking at individual executions.

The realtime results depend on the power and OS of the used system, which is why we recommend to first generate the
non-realtime results. By default, in realtime mode the system will preload all images. Depending on the RAM available
you should set the argument `maxPreloadImages`.