"""Download one Google Maps patch around a coordinate."""

import argparse
import os


DEFAULT_LAT = 47.535714
DEFAULT_LON = -52.752814
DEFAULT_ZOOM = 18
DEFAULT_PATCH_SIZE = 750
DEFAULT_OUTPUT_DIR = "output"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download a Google Maps satellite patch centered on a coordinate."
    )
    parser.add_argument("--lat", type=float, default=DEFAULT_LAT, help="Center latitude.")
    parser.add_argument("--lon", type=float, default=DEFAULT_LON, help="Center longitude.")
    parser.add_argument("--zoom", type=int, default=DEFAULT_ZOOM, help="Google Maps zoom level.")
    parser.add_argument(
        "--patch-size",
        type=int,
        default=DEFAULT_PATCH_SIZE,
        help="Output patch width and height in pixels.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the cropped PNG patch is saved.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    import google_map_downloader as gmaps

    gmaps.get_patch_from_GM(
        center_Lat=args.lat,
        center_Lon=args.lon,
        zoom=args.zoom,
        patch_save_root=args.output_dir,
        patch_size=args.patch_size,
    )


if __name__ == "__main__":
    main()
