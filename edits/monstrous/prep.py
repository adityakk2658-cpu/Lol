"""Decode the source clip to raw frames (VFR, true timestamps) and precompute
bidirectional optical flow between consecutive frames for slow-mo interpolation.

usage: python3 prep.py <source.mp4> <workdir>
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np

SRC_W, SRC_H = 2160, 3840          # portrait 4K after auto-rotation
FLOW_DIV = 4                       # flow computed at 1/4 resolution


def main(video, work):
    os.makedirs(work, exist_ok=True)
    pts = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
         "frame=pts_time", "-of", "csv=p=0", video],
        check=True, capture_output=True, text=True).stdout.split()
    pts = [float(p.strip(",")) for p in pts if p.strip(",")]

    raw = os.path.join(work, "frames.rgb")
    if not os.path.exists(raw) or os.path.getsize(raw) != len(pts) * SRC_W * SRC_H * 3:
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", video, "-fps_mode", "passthrough",
             "-vf", f"scale={SRC_W}:{SRC_H}:flags=lanczos", "-pix_fmt", "rgb24",
             "-f", "rawvideo", raw], check=True)
    n = os.path.getsize(raw) // (SRC_W * SRC_H * 3)
    assert n == len(pts), (n, len(pts))
    with open(os.path.join(work, "frames.json"), "w") as f:
        json.dump({"w": SRC_W, "h": SRC_H, "n": n, "pts": pts, "flow_div": FLOW_DIV}, f)

    # synced original audio (pads the 0.168 s audio start offset)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", video, "-af", "aresample=async=1:first_pts=0",
         "-ac", "2", "-ar", "48000", "-f", "f32le", os.path.join(work, "orig_audio.f32")],
        check=True)

    frames = np.memmap(raw, dtype=np.uint8, mode="r").reshape(n, SRC_H, SRC_W, 3)
    fw, fh = SRC_W // FLOW_DIV, SRC_H // FLOW_DIV
    fwd = np.lib.format.open_memmap(os.path.join(work, "flow_fwd.npy"), mode="w+",
                                    dtype=np.float16, shape=(n - 1, fh, fw, 2))
    bwd = np.lib.format.open_memmap(os.path.join(work, "flow_bwd.npy"), mode="w+",
                                    dtype=np.float16, shape=(n - 1, fh, fw, 2))
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    dis.setFinestScale(1)

    def gray(i):
        g = cv2.cvtColor(np.ascontiguousarray(frames[i]), cv2.COLOR_RGB2GRAY)
        return cv2.resize(g, (fw, fh), interpolation=cv2.INTER_AREA)

    prev = gray(0)
    for i in range(n - 1):
        nxt = gray(i + 1)
        fwd[i] = dis.calc(prev, nxt, None).astype(np.float16)
        bwd[i] = dis.calc(nxt, prev, None).astype(np.float16)
        prev = nxt
        if i % 40 == 0:
            print(f"flow {i}/{n - 1}", flush=True)
    fwd.flush(); bwd.flush()
    print("prep done:", n, "frames")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
