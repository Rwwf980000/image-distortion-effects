"""
Funny Mirrors: funhouse-mirror effects using a virtual camera.

Each mirror bends a flat 3D mesh by changing its Z coordinate with a
mathematical function (Gaussian, sine wave, or square root). A virtual
camera then "photographs" the bent surface, and the input image is
remapped onto it to produce the distorted result.

Usage:
    python funny_mirrors.py path/to/image.jpg
    python funny_mirrors.py path/to/image.jpg --mirrors 1 4 6 --output results
"""

import argparse
import os

import cv2
import numpy as np
from vcam import vcam, meshGen

SQRT_2PI = np.sqrt(2 * np.pi)


def gaussian(t, sigma=0.1):
    """Normal (bell-curve) profile used by mirrors 1-3."""
    return np.exp(-0.5 * (t / sigma) ** 2) / (sigma * SQRT_2PI)


# Each function returns the amount to ADD to the flat plane's Z coordinate.
MIRRORS = {
    1: ("Gaussian bump along X",
        lambda p: 20 * gaussian(p.X / p.W)),
    2: ("Gaussian dip along X",
        lambda p: -10 * gaussian(p.X / p.W)),
    3: ("Gaussian dip along Y",
        lambda p: -10 * gaussian(p.Y / p.W)),
    4: ("Sine waves on X and Y",
        lambda p: 20 * np.sin(2 * np.pi * (p.X - p.W / 4.0) / p.W)
        + 20 * np.sin(2 * np.pi * (p.Y - p.H / 4.0) / p.H)),
    5: ("Inverted sine waves",
        lambda p: -(20 * np.sin(2 * np.pi * (p.X - p.W / 4.0) / p.W)
                    - 20 * np.sin(2 * np.pi * (p.Y - p.H / 4.0) / p.H))),
    6: ("Square-root bowl",
        lambda p: -100 * np.sqrt((p.X / p.W) ** 2 + (p.Y / p.H) ** 2)),
}


def apply_mirror(img, z_offset):
    """Bend a plane by z_offset, view it with a virtual camera, and remap img."""
    h, w = img.shape[:2]
    camera = vcam(H=h, W=w)
    plane = meshGen(h, w)

    plane.Z += z_offset(plane)

    pts3d = plane.getPlane()
    pts2d = camera.project(pts3d)
    map_x, map_y = camera.getMaps(pts2d)
    return cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR)


def main():
    parser = argparse.ArgumentParser(description="Apply funny-mirror effects to an image.")
    parser.add_argument("image", help="path to the input image")
    parser.add_argument("--mirrors", type=int, nargs="+", default=sorted(MIRRORS),
                        choices=sorted(MIRRORS), help="which mirrors to apply (default: all)")
    parser.add_argument("--output", default="output", help="folder for results (default: output)")
    parser.add_argument("--show", action="store_true", help="also display each result in a window")
    args = parser.parse_args()

    img = cv2.imread(args.image)
    if img is None:
        raise SystemExit(f"Could not read image: {args.image}")

    os.makedirs(args.output, exist_ok=True)

    for n in args.mirrors:
        name, z_offset = MIRRORS[n]
        result = apply_mirror(img, z_offset)
        comparison = np.hstack((img, result))

        path = os.path.join(args.output, f"mirror{n}.jpg")
        cv2.imwrite(path, comparison)
        print(f"Mirror {n} ({name}) -> {path}")

        if args.show:
            cv2.imshow(f"Mirror {n}: {name}", comparison)
            cv2.waitKey(0)
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
