# Results

## Reading the numbers

Position error is mean absolute error on real images, in cm. Each model first gets one mean error per walk. Where several models are available, I report the mean ± sample standard deviation across training seeds. These error bars aren't confidence intervals or variation across streets.

The measured mean offsets are 0.03, 0.93, 1.93 and 3.07 m. The labels come from COLMAP, with scale fitted to the nominal walk spacing.

`W` uses 2D warps. `G` uses renders from World A, whose image training set contains the original path. `G2` uses World B, which includes the walk near 2 m. `R` uses real images from those two paths. `RG2` mixes those real images with World B renders.

Original path images are included in lane network training, so the first column isn't an independent test. Entries marked * use a walk included in reconstruction or lane network training.

## Real image evaluation

The base synthetic sets contain 6,000 generated images and use 15 epochs. The larger sets contain 20,000 and use 30 epochs. Real images from the original path are included in both.

| Model | Seeds | 0.03 m | 0.93 m | 1.93 m | 3.07 m |
|---|---|---|---|---|---|
| `W` | 3 | 2.0 ± 0.5 | 24.4 ± 2.0 | 73.9 ± 8.3 | 176.0 ± 9.8 |
| `G` | 3 | 1.9 ± 0.2 | 27.9 ± 2.7 | 56.0 ± 5.4 | 95.5 ± 10.3 |
| `G2` | 3 | 1.6 ± 0.2 | 23.6 ± 9.8 | 40.3 ± 10.4* | 79.1 ± 14.2 |
| `R` | 3 | 0.7 ± 0.1 | 10.0 ± 1.2 | 0.7 ± 0.1* | 149.3 ± 5.1 |
| `W_20k` † | 3 | 0.5 ± 0.0 | 2.9 ± 1.6 | 33.5 ± 10.7 | 134.8 ± 9.2 |
| `G_20k` | 3 | 0.5 ± 0.1 | 2.8 ± 0.9 | 6.6 ± 0.5 | 27.0 ± 1.7 |
| `G2_20k` | 3 | 0.6 ± 0.1 | 2.9 ± 0.8 | 6.5 ± 1.4* | 25.8 ± 4.4 |
| `RG2` † | 2 | 1.3 ± 0.7 | 3.9 ± 1.2 | 0.9 ± 0.2* | 47.4 ± 2.4 |

The stored source is [quality_all.csv](results/quality_all.csv). Rows marked † are recorded in the previous README but are missing from that CSV. The mixed run repeats its real training images four times.

At the furthest offset, the matched warp error is about five times the World A render error. This compares position error for this experiment, rather than driving performance.

Increasing the image count and epochs together lowered error for both methods. This doesn't separate the effect of more images from longer training.

## Tuned warp runs

The November 16 run added seeds for the 1.6 m height and tested a 1.8 m height. All entries below are position errors at 3.07 m.

| Model | Seeds | Error in cm |
|---|---|---|
| `W` | 3 | 176.0 ± 9.8 |
| `W_h16` † | 3 | 170.6 ± 14.1 |
| `W_h18` † | 1 | 157.5 |
| `W_20k` † | 3 | 134.8 ± 9.2 |
| `W20k_h16` † | 3 | 144.1 ± 4.4 |
| `G_20k` | 3 | 27.0 ± 1.7 |
| `G2_20k` | 3 | 25.8 ± 4.4 |

The November values marked † haven't been added to the stored result CSVs yet. The 1.8 m run has one seed, so it has no seed error bar.

None of the tested warp settings reached the render runs at this offset. The lowest warp mean is 134.8 cm, against 27.0 cm for World A renders. I haven't established which warp setting would work best on another street.

### Earlier height checks

These are the original single seed runs from [robust_summary.csv](results/robust_summary.csv), rather than the updated averages above.

| Warp camera height in m | Seeds | 0.03 m | 0.93 m | 1.93 m | 3.07 m |
|---|---|---|---|---|---|
| 1.2 | 1 | 1.5 | 21.6 | 77.1 | 166.2 |
| 1.6 | 1 | 1.9 | 4.0 | 41.8 | 155.3 |

Changing height can improve the nearer offsets. The original 1.6 m run had lower errors than the base render runs at 0.93 and 1.93 m. That doesn't establish a reliable advantage across seeds.

## Reconstruction checks

I rebuilt World A using sparse points observed by at least two cameras from the original path. This changes the initialization points, but the camera poses still come from the shared reconstruction.

| Model | Seeds | 0.03 m | 0.93 m | 1.93 m | 3.07 m |
|---|---|---|---|---|---|
| `G_strict` | 1 | 1.4 | 29.3 | 61.1 | 100.5 |
| `G_big` | 1 | 2.0 | 35.4 | 69.1 | 113.5 |
| `G2_big` | 1 | 1.6 | 28.8 | 49.4* | 88.6 |

The sources are [quality_q1.csv](results/quality_q1.csv) and [quality_q2.csv](results/quality_q2.csv).

The strict run's furthest error is near the base render mean of 95.5 ± 10.3 cm. One seed doesn't rule out leakage. The larger reconstruction settings didn't lower lane error in these single seed comparisons.

## Image quality

The original sampled evaluation gives the following PSNR values in dB.

| Reconstruction | Original path | Slow repeat | 0.93 m | 1.93 m | 3.07 m |
|---|---|---|---|---|---|
| A | 23.36 | 24.89 | 20.37 | 18.93 | 17.49 |
| B | 23.14 | 24.55 | 22.06 | Training images | 19.47 |
| A with larger model | 23.62 | 25.37 | 20.19 | 18.88 | 17.47 |
| B with larger model | 23.32 | 24.80 | 22.07 | Training images | 19.49 |

These means come from the four `results/by_offset_*.csv` files. World A has 257 evaluated frames and World B has 194 in these sampled files.

Adding the walk near 2 m raises the sampled PSNR at 0.93 m by 1.69 dB and at 3.07 m by 1.98 dB.

| Evaluation | World | PSNR in dB | SSIM | LPIPS |
|---|---|---|---|---|
| Original sampled evaluation | A | 19.94 | 0.544 | 0.453 |
| Original sampled evaluation | B | 21.59 | 0.611 | 0.402 |
| All frames rerun on October 30 † | A | 19.51 | 0.527 | 0.466 |
| All frames rerun on October 30 † | B | 21.25 | 0.599 | 0.409 |

Higher PSNR and SSIM are better. Lower LPIPS is better.

The original aggregates are in [walk0.json](results/walk0.json) and [walk02.json](results/walk02.json). The all frames rerun values are recorded separately and its output files aren't in this checkout. Its reported PSNR means per walk differ from the sampled evaluation by no more than 0.03 dB. That comparison needs the missing rerun CSVs to check.

The two evaluations weight different frame sets, so I keep their overall averages separate.

## Closed loop inside the reconstruction

For each network, I tested five positions along the street with two initial offsets, in each world. Each rollout takes 40 steps of 0.5 m. Heading changes are capped at 5 degrees per step. Success means ending less than 30 cm from the target.

| Target offset in m | World | `W` | `G` | `G2` |
|---|---|---|---|---|
| 0 | A | 0/10 | 10/10 | 10/10 |
| 0 | B | 0/10 | 10/10 | 10/10 |
| 1.5 | A | 4/10 | 10/10 | 10/10 |
| 1.5 | B | 2/10 | 10/10 | 10/10 |

Across both targets and worlds, each render network succeeds in 40/40 rollouts. The warp network succeeds in 6/40. Together, the two render networks account for 80/80 rollouts.

For the zero target, the warp network ends an average of 11.93 m away in World A and 12.70 m in World B.

The sources are [closed_loop_summary.csv](results/closed_loop_summary.csv) and [cl_road_summary.csv](results/cl_road_summary.csv). These runs use the base networks, rather than the 20,000 image models.

The simulation produces the kind of image used to train the render networks. It favours them and doesn't establish performance on a real car.

The demo replays selected trajectories inside the larger world built from all walks. The replay script selects the render run with the smallest final error and pairs it with the matching warp start. It's an illustration rather than a random sample.

## Half street

I trained a reconstruction on the first half of the street, then trained a lane network with 20,000 renders for 30 epochs. I evaluated it on real frames from the other half. The full street networks below are evaluated on those same frames.

| Model | Seeds | 0.03 m | 0.93 m | 1.93 m | 3.07 m |
|---|---|---|---|---|---|
| `G_half` | 1 | 0.7 | 4.5 | 32.1 | 100.1 |
| `G_20k` | 3 | 0.6 ± 0.1 | 3.0 ± 1.5 | 3.7 ± 0.8 | 30.4 ± 2.0 |
| `G` | 3 | 1.9 ± 0.1 | 25.6 ± 1.6 | 53.6 ± 5.9 | 100.9 ± 11.1 |
| `W` | 3 | 1.9 ± 0.6 | 23.0 ± 4.7 | 71.7 ± 9.9 | 186.6 ± 8.5 |

The source is [half_street.csv](results/half_street.csv). The half street model has about 3.3 times the full street model's error at the furthest offset. This check has one seed and doesn't test another street.

## Capture and training details

I filmed on October 28, 2026. The [capture protocol](capture/PROTOCOL.md) records four parallel walks, a slow repeat and a sideways sweep. The six clips contribute 878 frames at 3 frames per second. The original reconstruction reports 330 training images for World A and 457 for World B.

The reconstruction jobs use 30,000 iterations. Synthetic cameras sample offsets uniformly between 0 and 3 m and headings between minus 10 and 15 degrees. Network images are 480 by 270 pixels.

The network predicts offset and heading using an ImageNet initialized ResNet18. Training uses L1 loss, AdamW, a one cycle learning rate schedule and brightness augmentation. A fixed random split reserves a tenth of each image set for validation. The real image reference repeats its training set ten times.

Seeds change network training, while the generated image sets and validation split stay fixed. The error bars therefore don't cover variation in filming, reconstruction or synthetic data generation.

## Limitations

`choose_world.py` picks the world using the test walks `w1` and `w3`. This is selection leakage, and I plan to fix it with a separate validation split.

`pick_q4.py` uses those walks to choose which variants receive extra seeds too.

All walks contributed to camera pose estimation. Restricting the images used to train a splat doesn't remove that dependence. The scale is fitted to the planned spacing rather than independently measured ground truth.

Everything comes from one street in one filming session. I haven't tested another street, weather or lighting. I filmed while walking with a phone at chest height, rather than driving with a car camera.

The original path images point slightly right, reducing coverage on the left. Parked cars may have moved between passes. These can affect the reconstructed views.

## Reproduction and available files

The working scripts import each other from one flat directory. They expect the original workspace layout, including `raw/`, `frames3/`, `proc3/`, `split_*/`, `outputs/` and `lane/`.

The repo doesn't include the raw captures, processed camera map, reconstruction checkpoints or trained lane checkpoints. The [published viewer export](https://huggingface.co/datasets/mohsem/splat2lane-street) doesn't replace these inputs.

| Stage | Recorded scripts |
|---|---|
| Extract frames, map cameras and train worlds | `pipeline/s3d_poses.sh`, `pipeline/colmap_relaxed.sh` |
| Evaluate worlds and build the display world | `pipeline/s3d_after.sh`, `pipeline/s3d_bigfresh.sh` |
| Generate images and train base networks | `pipeline/run_lane.sh` |
| Multiple starts, seeds, heights and road target | `pipeline/run_extra.sh`, `pipeline/run_robust.sh`, `pipeline/run_road.sh` |
| Strict points, larger worlds and more renders | `pipeline/run_quality.sh`, `pipeline/run_resume.sh` |
| Evaluate all nontraining image frames | `pipeline/run_allfr.sh`, `pipeline/run_allfr2.sh` |
| Mixed real and rendered training images | `pipeline/run_mix.sh` |
| Render the demo and export the viewer world | `pipeline/run_final.sh` |

These are records of local jobs, with absolute paths, fixed output names and waits for other jobs. They need adapting before reuse. The container tag is `latest`, so the repo doesn't pin the original environment.

The half street runner, matched warp runner, November tuned warp runner and their complete outputs aren't included. The historical tables above retain results that need those files for full reproduction.

The stored [run summary](results/SUMMARY.md) contains earlier snapshots, including single seed results that later received extra seeds. [Training curves](results/training_curves/) record the network training runs.

## Sources and related work

The reconstruction uses [COLMAP](https://colmap.github.io/), [3D Gaussian Splatting](https://arxiv.org/abs/2308.04079), [Nerfstudio](https://arxiv.org/abs/2302.04264) and [gsplat](https://arxiv.org/abs/2409.06765). Image quality includes [LPIPS](https://arxiv.org/abs/1801.03924).

The 2D baseline is my implementation of image warping inspired by [The NVIDIA PilotNet Experiments](https://arxiv.org/abs/2010.08776). It isn't a reproduction of NVIDIA's complete system.

Related work links include [UniSim](https://arxiv.org/abs/2308.01898), [HUGSIM](https://arxiv.org/abs/2412.01718), [RAD](https://arxiv.org/abs/2502.13144), [Para Lane](https://arxiv.org/abs/2502.15635), [EUVS](https://openaccess.thecvf.com/content/ICCV2025/papers/Han_Extrapolated_Urban_View_Synthesis_Benchmark_ICCV_2025_paper.pdf) and [MTGS](https://arxiv.org/abs/2503.12552).
