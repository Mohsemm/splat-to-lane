#!/bin/bash
# colmap mapper with relaxed init
if [ "$1" = mapper ]; then exec colmap "$@" --Mapper.init_min_tri_angle 2 --Mapper.init_min_num_inliers 50 --Mapper.abs_pose_min_num_inliers 15; else exec colmap "$@"; fi
