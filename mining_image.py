"""Download Google Maps patches centered on Canadian mining polygons.

This script reads the Maus et al. 2022 global mining polygons GeoPackage,
filters Canadian mines, and downloads centered 750 x 750 image patches using
the existing Google Maps downloader.
"""

import argparse
import os
import sqlite3
import struct
from dataclasses import dataclass


DEFAULT_GPKG = os.path.join(
    "Maus-etal_2022_V2_allfiles",
    "global_mining_polygons_v2.gpkg",
)
DEFAULT_OUTPUT_DIR = os.path.join("output", "mining_images")
DEFAULT_COUNTRY = "CAN"
DEFAULT_ZOOM = 18
DEFAULT_PATCH_SIZE = 750


@dataclass(frozen=True)
class MinePolygon:
    fid: int
    country_code: str
    country_name: str
    area: float
    min_lon: float
    max_lon: float
    min_lat: float
    max_lat: float

    @property
    def center_lat(self):
        return (self.min_lat + self.max_lat) / 2.0

    @property
    def center_lon(self):
        return (self.min_lon + self.max_lon) / 2.0


def gpkg_envelope(geom):
    """Return (min_lon, max_lon, min_lat, max_lat) from a GeoPackage geometry."""
    if geom[:2] != b"GP":
        raise ValueError("Geometry is not GeoPackage binary.")

    flags = geom[3]
    endian = "<" if flags & 1 else ">"
    envelope_type = (flags >> 1) & 7
    if envelope_type == 0:
        raise ValueError("Geometry has no stored envelope.")

    envelope_sizes = {1: 32, 2: 48, 3: 48, 4: 64}
    envelope_size = envelope_sizes.get(envelope_type)
    if envelope_size is None:
        raise ValueError(f"Unsupported GeoPackage envelope type: {envelope_type}")

    envelope = struct.unpack(endian + "dddd", geom[8:40])
    return envelope[0], envelope[1], envelope[2], envelope[3]


def load_mines(gpkg_path, country_code=DEFAULT_COUNTRY):
    query = """
        SELECT fid, geom, ISO3_CODE, COUNTRY_NAME, AREA
        FROM mining_polygons
        WHERE ISO3_CODE = ?
        ORDER BY AREA DESC
    """

    mines = []
    with sqlite3.connect(gpkg_path) as connection:
        for fid, geom, iso3, country_name, area in connection.execute(query, (country_code,)):
            min_lon, max_lon, min_lat, max_lat = gpkg_envelope(geom)
            mine = MinePolygon(
                fid=fid,
                country_code=iso3,
                country_name=country_name,
                area=area,
                min_lon=min_lon,
                max_lon=max_lon,
                min_lat=min_lat,
                max_lat=max_lat,
            )
            mines.append(mine)
    return mines


def load_fid_metadata(gpkg_path, fid):
    query = """
        SELECT fid, ISO3_CODE, COUNTRY_NAME, AREA
        FROM mining_polygons
        WHERE fid = ?
    """

    with sqlite3.connect(gpkg_path) as connection:
        return connection.execute(query, (fid,)).fetchone()


def select_mines(mines, country_code=DEFAULT_COUNTRY, fid=None, limit=1):
    if fid is not None:
        selected = [mine for mine in mines if mine.fid == fid]
        if not selected:
            raise ValueError(f"No {country_code} mine polygon found with fid={fid}.")
        return selected
    return mines[:limit]


def format_mine(mine):
    return (
        "fid={fid} area={area:.3f} center=({lat:.6f}, {lon:.6f}) bounds=({min_lat:.6f}, "
        "{min_lon:.6f})-({max_lat:.6f}, {max_lon:.6f})".format(
            fid=mine.fid,
            area=mine.area,
            lat=mine.center_lat,
            lon=mine.center_lon,
            min_lat=mine.min_lat,
            min_lon=mine.min_lon,
            max_lat=mine.max_lat,
            max_lon=mine.max_lon,
        )
    )


def list_mines(mines):
    for mine in mines:
        print(format_mine(mine))


def mine_output_path(output_dir, mine):
    lat = f"{mine.center_lat:.6f}"
    lon = f"{mine.center_lon:.6f}"
    return os.path.join(output_dir, f"mine_{mine.fid}_Lat_{lat}_Lon_{lon}.png")


def download_mine(mine, zoom, patch_size, output_dir):
    import google_map_downloader as gmaps

    temporary_path = gmaps.get_patch_from_GM(
        center_Lat=round(mine.center_lat, 6),
        center_Lon=round(mine.center_lon, 6),
        zoom=zoom,
        patch_save_root=output_dir,
        patch_size=patch_size,
    )

    final_path = mine_output_path(output_dir, mine)
    if temporary_path != final_path:
        os.replace(temporary_path, final_path)
    return final_path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download 750 x 750 satellite patches for Canadian mining polygons."
    )
    parser.add_argument("--gpkg", default=DEFAULT_GPKG, help="Path to the Maus mining polygons GeoPackage.")
    parser.add_argument("--country", default=DEFAULT_COUNTRY, help="ISO3 country code to filter.")
    parser.add_argument("--fid", type=int, help="Download a specific polygon fid.")
    parser.add_argument("--limit", type=int, default=1, help="Number of largest matching polygons to download.")
    parser.add_argument("--zoom", type=int, default=DEFAULT_ZOOM, help="Google Maps zoom level.")
    parser.add_argument("--patch-size", type=int, default=DEFAULT_PATCH_SIZE, help="Output patch width and height.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory where PNG patches are saved.")
    parser.add_argument("--list-only", action="store_true", help="Print selected mine centers without downloading.")
    parser.add_argument("--list-all", action="store_true", help="Print every matching mine fid and center without downloading.")
    return parser.parse_args()


def main():
    args = parse_args()
    mines = load_mines(args.gpkg, country_code=args.country)
    print(f"Loaded {len(mines)} {args.country} mining polygons.")

    if args.list_all:
        list_mines(mines)
        return

    try:
        selected = select_mines(mines, country_code=args.country, fid=args.fid, limit=args.limit)
    except ValueError as exc:
        if args.fid is None:
            raise
        metadata = load_fid_metadata(args.gpkg, args.fid)
        if metadata is None:
            raise SystemExit(str(exc)) from exc

        fid, iso3, country_name, area = metadata
        raise SystemExit(
            f"No {args.country} mine polygon found with fid={fid}. "
            f"That fid belongs to {country_name} ({iso3}), area={area:.3f}."
        ) from exc

    for mine in selected:
        print(format_mine(mine))

    if args.list_only:
        return

    os.makedirs(args.output_dir, exist_ok=True)
    for mine in selected:
        output_path = download_mine(
            mine=mine,
            zoom=args.zoom,
            patch_size=args.patch_size,
            output_dir=args.output_dir,
        )
        print(f"Mine patch saved: {output_path}")


if __name__ == "__main__":
    main()
