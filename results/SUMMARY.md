# Street-in-3D night run summary (2026-10-28/29)

Offsets in cm = mean absolute error of the lane-position net on REAL frames; walks at 0.03 / 0.93 / 1.93 / 3.07 m (COLMAP). Caveats: R trained on walk 2; G2/B worlds saw walk 2; closed loops run inside splat worlds (render domain).

## First run: W / G / G2 / R on real walks
`lane/results/real_errors.csv`

| set | walk | true_offset_m | n | offset_mae_cm | offset_median_cm | heading_mae_deg | mean_pred_offset_m |
|---|---|---|---|---|---|---|---|
| W | w0 | 0.03 | 140 | 2.4 | 2.2 | 0.11 | 0.01 |
| W | w1 | 0.93 | 156 | 22.2 | 21.9 | 2.63 | 0.7 |
| W | w2 | 1.93 | 127 | 65.1 | 64.2 | 7.56 | 1.28 |
| W | w3 | 3.07 | 140 | 164.7 | 156.2 | 10.23 | 1.42 |
| G | w0 | 0.03 | 140 | 2.0 | 1.8 | 0.11 | 0.01 |
| G | w1 | 0.93 | 156 | 25.1 | 25.3 | 0.53 | 0.68 |
| G | w2 | 1.93 | 127 | 49.9 | 48.2 | 1.82 | 1.43 |
| G | w3 | 3.07 | 140 | 83.7 | 82.5 | 3.62 | 2.23 |
| G2 | w0 | 0.03 | 140 | 1.7 | 1.4 | 0.11 | 0.02 |
| G2 | w1 | 0.93 | 156 | 12.7 | 12.0 | 0.29 | 0.8 |
| G2 | w2 | 1.93 | 127 | 28.5 | 28.5 | 0.96 | 1.65 |
| G2 | w3 | 3.07 | 140 | 63.4 | 59.0 | 2.38 | 2.43 |
| R | w0 | 0.03 | 140 | 0.9 | 0.6 | 0.08 | 0.02 |
| R | w1 | 0.93 | 156 | 9.7 | 10.8 | 1.01 | 0.83 |
| R | w2 | 1.93 | 127 | 0.8 | 0.5 | 0.03 | 1.93 |
| R | w3 | 3.07 | 140 | 151.9 | 152.1 | 4.13 | 1.55 |

## Seeds (3 per net) + W warp height 1.2 / 1.6 m (mean +- std cm)
`lane/results/robust_summary.csv`

| group | walk | n_models | offset_mae_mean_cm | offset_mae_std_cm |
|---|---|---|---|---|
| W | w0 | 3 | 2.0 | 0.5 |
| W | w1 | 3 | 24.4 | 2.0 |
| W | w2 | 3 | 73.9 | 8.3 |
| W | w3 | 3 | 176.0 | 9.8 |
| G | w0 | 3 | 1.9 | 0.2 |
| G | w1 | 3 | 27.9 | 2.7 |
| G | w2 | 3 | 56.0 | 5.4 |
| G | w3 | 3 | 95.5 | 10.3 |
| G2 | w0 | 3 | 1.6 | 0.2 |
| G2 | w1 | 3 | 23.6 | 9.8 |
| G2 | w2 | 3 | 40.3 | 10.4 |
| G2 | w3 | 3 | 79.1 | 14.2 |
| R | w0 | 3 | 0.7 | 0.1 |
| R | w1 | 3 | 10.0 | 1.2 |
| R | w2 | 3 | 0.7 | 0.1 |
| R | w3 | 3 | 149.3 | 5.1 |
| W_h1.2 | w0 | 1 | 1.5 | 0.0 |
| W_h1.2 | w1 | 1 | 21.6 | 0.0 |
| W_h1.2 | w2 | 1 | 77.1 | 0.0 |
| W_h1.2 | w3 | 1 | 166.2 | 0.0 |
| W_h1.6 | w0 | 1 | 1.9 | 0.0 |
| W_h1.6 | w1 | 1 | 4.0 | 0.0 |
| W_h1.6 | w2 | 1 | 41.8 | 0.0 |
| W_h1.6 | w3 | 1 | 155.3 | 0.0 |

## Closed loop, target 0 m (walk-0 line), 10 starts/net/world
`lane/results/closed_loop_summary.csv`

| world | set | successes | runs | mean_final_abs_offset_m |
|---|---|---|---|---|
| A | W | 0 | 10 | 11.93 |
| A | G | 10 | 10 | 0.03 |
| A | G2 | 10 | 10 | 0.02 |
| B | W | 0 | 10 | 12.7 |
| B | G | 10 | 10 | 0.02 |
| B | G2 | 10 | 10 | 0.03 |

## Closed loop, target 1.5 m (in the road), 10 starts/net/world
`lane/results/cl_road_summary.csv`

| world | set | successes | runs | mean_final_abs_offset_m |
|---|---|---|---|---|
| A | W | 4 | 10 | 0.34 |
| A | G | 10 | 10 | 0.02 |
| A | G2 | 10 | 10 | 0.04 |
| B | W | 2 | 10 | 0.36 |
| B | G | 10 | 10 | 0.03 |
| B | G2 | 10 | 10 | 0.02 |

## Q1 strict world A (points seen only by walk 0)
`lane/results/quality_q1.csv`

| variant | n_models | w0_cm | w1_cm | w2_cm | w3_cm |
|---|---|---|---|---|---|
| G | 3 | 1.9+-0.2 | 27.9+-2.7 | 56.0+-5.4 | 95.5+-10.3 |
| G2 | 3 | 1.6+-0.2 | 23.6+-9.8 | 40.3+-10.4 | 79.1+-14.2 |
| G_strict | 1 | 1.4 | 29.3 | 61.1 | 100.5 |

## Q2 splatfacto-big worlds
`lane/results/quality_q2.csv`

| variant | n_models | w0_cm | w1_cm | w2_cm | w3_cm |
|---|---|---|---|---|---|
| G | 3 | 1.9+-0.2 | 27.9+-2.7 | 56.0+-5.4 | 95.5+-10.3 |
| G2 | 3 | 1.6+-0.2 | 23.6+-9.8 | 40.3+-10.4 | 79.1+-14.2 |
| G_big | 1 | 2.0 | 35.4 | 69.1 | 113.5 |
| G2_big | 1 | 1.6 | 28.8 | 49.4 | 88.6 |

## Q3 20k renders, 30 epochs
`lane/results/quality_q3.csv`

| variant | n_models | w0_cm | w1_cm | w2_cm | w3_cm |
|---|---|---|---|---|---|
| G | 3 | 1.9+-0.2 | 27.9+-2.7 | 56.0+-5.4 | 95.5+-10.3 |
| G2 | 3 | 1.6+-0.2 | 23.6+-9.8 | 40.3+-10.4 | 79.1+-14.2 |
| G_strict | 1 | 1.4 | 29.3 | 61.1 | 100.5 |
| G_big | 1 | 2.0 | 35.4 | 69.1 | 113.5 |
| G2_big | 1 | 1.6 | 28.8 | 49.4 | 88.6 |
| G_20k | 1 | 0.5 | 1.8 | 6.3 | 26.7 |
| G2_20k | 1 | 0.5 | 2.3 | 5.8 | 20.8 |

## ALL variants (seed mean +- std where available)
`lane/results/quality_all.csv`

| variant | n_models | w0_cm | w1_cm | w2_cm | w3_cm |
|---|---|---|---|---|---|
| W | 3 | 2.0+-0.5 | 24.4+-2.0 | 73.9+-8.3 | 176.0+-9.8 |
| G | 3 | 1.9+-0.2 | 27.9+-2.7 | 56.0+-5.4 | 95.5+-10.3 |
| G2 | 3 | 1.6+-0.2 | 23.6+-9.8 | 40.3+-10.4 | 79.1+-14.2 |
| R | 3 | 0.7+-0.1 | 10.0+-1.2 | 0.7+-0.1 | 149.3+-5.1 |
| G_strict | 1 | 1.4 | 29.3 | 61.1 | 100.5 |
| G_big | 1 | 2.0 | 35.4 | 69.1 | 113.5 |
| G2_big | 1 | 1.6 | 28.8 | 49.4 | 88.6 |
| G_20k | 3 | 0.5+-0.1 | 2.8+-0.9 | 6.6+-0.5 | 27.0+-1.7 |
| G2_20k | 3 | 0.6+-0.1 | 2.9+-0.8 | 6.5+-1.4 | 25.8+-4.4 |

Render quality by_offset_walk0.csv: w0 23.36 dB, w0b 24.89 dB, w1 20.37 dB, w2 18.93 dB, w3 17.49 dB

Render quality by_offset_walk02.csv: w0 23.14 dB, w0b 24.55 dB, w1 22.06 dB, w3 19.47 dB

Render quality by_offset_walk02big.csv: w0 23.32 dB, w0b 24.80 dB, w1 22.07 dB, w3 19.49 dB

Render quality by_offset_walk0big.csv: w0 23.62 dB, w0b 25.37 dB, w1 20.19 dB, w2 18.88 dB, w3 17.47 dB

q3_choice.txt: G G outputs/street_walk0/splatfacto/2026-10-28_204550/config.yml 61.7; G2 G2 outputs/street_walk02/splatfacto/2026-10-28_212103/config.yml 51.3; 

q4_pick.txt: G2_20k G2 lane/renders_G220k 30; G_20k G lane/renders_G20k 30; 

## Job durations and temperatures
- quality-20261029-0509.log: strict_points 0m08s
- quality-20261029-0751.log: strict_points 0m09s, world_street_walk0_strict 35m54s, render_Astrict 1m45s, train_G_strict 4m49s, eval_q1 0m09s, world_street_walk0_big 129m11s, world_street_walk02_big 323m28s | == skipped (ABORT/late): evalA_big; == skipped (ABORT/late): evalB_big; == skipped (ABORT/late): curve_big; == skipped (ABORT/late): render_Abig; == skipped (ABORT/late): render_Bbig; == skipped (ABORT/late): train_G_big; == skipped (ABORT/late): train_G2_big; == skipped (ABORT/late): eval_q2; == skipped (ABORT/late): choose; == skipped (ABORT/late): eval_q3
- resume-20261029-2200.log:  | == Thu Oct 29 22:00:56 +04 2026 START resume (skipped quality steps; window until 08:00 Toronto = 16:00 PC)
- resume-20261029-2218.log: evalA_big 6m29s, evalB_big 4m54s, curve_big 2m08s, render_Abig 2m29s, render_Bbig 2m21s, train_G_big 2m42s, train_G2_big 2m43s, eval_q2 0m10s, choose 0m00s, render_G20k 3m23s, train_G_20k 16m30s, render_G220k 3m22s, train_G2_20k 16m30s, eval_q3 0m11s, train_G2_20k_s1 16m29s, train_G2_20k_s2 16m28s, train_G_20k_s1 16m30s, train_G_20k_s2 16m32s | == Thu Oct 29 22:18:06 +04 2026 START resume (skipped quality steps; window until 08:00 Toronto = 16:00 PC)

Files: lane/results/ (plots *.png, videos *.mp4, demo_hd.mp4), lane/models/, exports/street_all_1080b/{splat,splat_yup}.ply
