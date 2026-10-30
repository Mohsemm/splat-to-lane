# Capture protocol (as filmed, Wed 28 Oct 2026)

**Where.** Robert St, Toronto, north of Russell St (Russell to the straight part before Sappers Ln), walking north. Walk 0 follows the west curb, where no cars were parked. Walks 1-3 are in the road, parallel to walk 0, done when the road was clear. Parked cars were on the east side.

**When.** 11:20 to 12:10.

**Phone.** iPhone, main 1x lens, 4K (3840x2160) at 30 fps. AE/AF lock on the grey road past the "SCHOOL" marking (~10 m ahead). HDR off, stabilisation off, Lock Camera and Lock White Balance on, Auto FPS off. Held in landscape with both hands at chest height (~1.3 m), pointed straight down the street like a dashcam.

**Passes** (all northbound, recording stopped on the way back):

| clip | what | length | frames used (3 fps) | offset from walk 0 (COLMAP) |
|---|---|---|---|---|
| w0 | walk 0, normal pace | 47 s | 140 | 0.03 m |
| w0b | walk 0, slow | 78 s | 236 | ≈0 m (w0 + w0b define the line) |
| w1 | walk 1 | 52 s | 156 | 0.93 m |
| w2 | walk 2 | 42 s | 127 | 1.93 m |
| w3 | walk 3 | 47 s | 140 | 3.07 m |
| sweep | slow sidestep across all four lines | 25 s | 79 | joins the walks into one map |

The nominal offsets were 0, 1, 2 and 3 m. The test labels come from the COLMAP reconstruction: the walk-0 line is fitted through all w0 + w0b camera positions, and the metric scale is the least-squares fit of the measured walk spacing to the nominal 1/2/3 m (`scripts/lane_common.py`, `fit_geometry`). That gives the offsets in the table. The posed stretch is about 31 m long.

**People passing.** Keep recording. Stop walking until they pass, then carry on at the same pace.

**Things that went off-plan.**
- Both walk-0 clips are yawed slightly to the right. Walks 2 and 3 point straight ahead. COLMAP solves the yaw per frame, so the main cost is less coverage of the left edge.
- A car with a trailer was parked on the walking side, so the stretch was moved north past it.
- The sweep was filmed 20 minutes after walk 3 because a truck was parked mid-road. Anything that moved in that gap (parked cars) is geometry no walk saw consistently.
