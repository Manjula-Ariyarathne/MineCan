"""Download one centered Google Maps satellite patch."""

import io
import math
import os
import random
import time
import urllib.request as ur
from threading import Thread

import PIL.Image as pil


DEFAULT_PATCH_SIZE = 750
DEFAULT_STYLE = "s"
DEFAULT_SOURCE = "Google"
MAX_LATITUDE = 85.0511287798
TILE_SIZE = 256

MAP_URLS = {
    "Google": "http://mts0.googleapis.com/vt?lyrs={style}&x={x}&y={y}&z={z}",
}


def is_image_data(data):
    """Return True when bytes can be opened as an image."""
    try:
        with pil.open(io.BytesIO(data)) as image:
            image.verify()
        return True
    except Exception:
        return False


def wgs_to_tile(lon, lat, zoom):
    """Convert WGS84 longitude/latitude to a Google tile index."""
    if not isinstance(zoom, int) or zoom < 0 or zoom > 22:
        raise ValueError("zoom must be an integer between 0 and 22.")

    lat = max(min(lat, MAX_LATITUDE), -MAX_LATITUDE)
    lat_rad = math.radians(lat)
    num_tiles = 2 ** zoom

    x = math.floor((lon + 180.0) / 360.0 * num_tiles)
    y = math.floor(
        (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi)
        / 2.0
        * num_tiles
    )

    max_tile = num_tiles - 1
    if not (0 <= x <= max_tile and 0 <= y <= max_tile):
        raise ValueError(f"Invalid tile coordinates: x={x}, y={y} (z={zoom})")

    return x, y


def wgs_to_pixel(lon, lat, zoom):
    """Convert WGS84 longitude/latitude to global Google pixel coordinates."""
    lat = max(min(lat, MAX_LATITUDE), -MAX_LATITUDE)
    sin_lat = math.sin(math.radians(lat))
    scale = TILE_SIZE * (2 ** zoom)

    x = (lon + 180.0) / 360.0 * scale
    y = (0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi)) * scale
    return math.floor(x), math.floor(y)


def tile_radius_for_patch(patch_size):
    """Return how many surrounding tiles are needed for a centered patch."""
    if patch_size <= 0:
        raise ValueError("patch_size must be greater than 0.")
    return max(1, math.ceil((patch_size / 2) / TILE_SIZE))


def tile_frame(center_x, center_y, radius):
    """Return the tile frame around the center tile."""
    return {
        "LT": (center_x - radius, center_y - radius),
        "RB": (center_x + radius, center_y + radius),
    }


def get_url(source, x, y, z, style):
    try:
        template = MAP_URLS[source]
    except KeyError as exc:
        raise ValueError(f"Unknown map source: {source}") from exc
    return template.format(x=x, y=y, z=z, style=style)


def build_tile_urls(lat, lon, zoom, source=DEFAULT_SOURCE, style=DEFAULT_STYLE, patch_size=DEFAULT_PATCH_SIZE):
    """Build a fixed-size tile URL grid around the requested coordinate."""
    center_x, center_y = wgs_to_tile(lon, lat, zoom)
    radius = tile_radius_for_patch(patch_size)
    frame = tile_frame(center_x, center_y, radius)
    lt_x, lt_y = frame["LT"]
    rb_x, rb_y = frame["RB"]
    max_tile = 2 ** zoom - 1

    urls = []
    for y in range(lt_y, rb_y + 1):
        for x in range(lt_x, rb_x + 1):
            if 0 <= x <= max_tile and 0 <= y <= max_tile:
                urls.append(get_url(source, x, y, zoom, style))
            else:
                urls.append(None)

    print(f"Center tile: {center_x}, {center_y}")
    print(f"Tile grid: {rb_x - lt_x + 1} x {rb_y - lt_y + 1}")
    return urls, frame


class TileDownloader(Thread):
    def __init__(self, index, count, urls, datas):
        super().__init__()
        self.index = index
        self.count = count
        self.urls = urls
        self.datas = datas

    def download(self, url):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/101.0.4951.54 Safari/537.36"
            ),
            "Referer": "https://www.google.com/maps/",
        }

        for retry in range(3):
            try:
                request = ur.Request(url, headers=headers)
                with ur.urlopen(request, timeout=10) as response:
                    if response.status != 200:
                        print(f"Skip HTTP {response.status}: {url}")
                        return None

                    data = response.read()
                    if len(data) < 1024 or not is_image_data(data):
                        print(f"Invalid image data: {url}")
                        return None

                    return data
            except Exception as e:
                print(f"Download failed ({retry + 1}/3): {str(e)[:60]} - {url}")
                time.sleep(random.uniform(0.5, 1.5))

        return None

    def run(self):
        for i, url in enumerate(self.urls):
            if i % self.count != self.index or url is None:
                continue

            time.sleep(random.uniform(0.1, 0.5))
            self.datas[i] = self.download(url)


def download_tiles(urls, max_workers=4):
    datas = [None] * len(urls)
    valid_url_count = sum(url is not None for url in urls)
    worker_count = min(max_workers, max(1, valid_url_count))
    tasks = [TileDownloader(i, worker_count, urls, datas) for i in range(worker_count)]

    for task in tasks:
        task.start()
    for task in tasks:
        task.join()

    print(f"Downloaded {sum(data is not None for data in datas)}/{valid_url_count} tiles")
    return datas


def merge_tiles(datas, frame):
    lt_x, lt_y = frame["LT"]
    rb_x, rb_y = frame["RB"]
    width_tiles = rb_x - lt_x + 1
    height_tiles = rb_y - lt_y + 1
    mosaic = pil.new("RGB", (width_tiles * TILE_SIZE, height_tiles * TILE_SIZE))

    for i, data in enumerate(datas):
        if data is None:
            continue

        try:
            with pil.open(io.BytesIO(data)) as tile:
                x = i % width_tiles
                y = i // width_tiles
                mosaic.paste(tile.convert("RGB"), (x * TILE_SIZE, y * TILE_SIZE))
        except Exception as e:
            print(f"Skip corrupted tile {i}: {str(e)[:60]}")

    return mosaic


def crop_center_patch(mosaic, frame, lat, lon, zoom, patch_size):
    lt_x, lt_y = frame["LT"]
    global_x, global_y = wgs_to_pixel(lon, lat, zoom)
    mosaic_x = global_x - lt_x * TILE_SIZE
    mosaic_y = global_y - lt_y * TILE_SIZE

    half_before = patch_size // 2
    half_after = patch_size - half_before
    box = (
        mosaic_x - half_before,
        mosaic_y - half_before,
        mosaic_x + half_after,
        mosaic_y + half_after,
    )

    patch = mosaic.crop(box)
    if patch.size != (patch_size, patch_size):
        raise RuntimeError(f"Patch crop failed; expected {(patch_size, patch_size)}, got {patch.size}")
    return patch


def patch_output_path(output_dir, lat, lon):
    return os.path.join(output_dir, f"Lat_{lat}_Lon_{lon}.png")


def get_patch_from_GM(
    center_Lat,
    center_Lon,
    zoom,
    tif_save_path=None,
    patch_save_root="output",
    patch_size=DEFAULT_PATCH_SIZE,
):
    """Download and save a square satellite patch centered on a coordinate."""
    start_time = time.time()
    os.makedirs(patch_save_root, exist_ok=True)

    urls, frame = build_tile_urls(center_Lat, center_Lon, zoom, patch_size=patch_size)
    datas = download_tiles(urls)
    mosaic = merge_tiles(datas, frame)
    patch = crop_center_patch(mosaic, frame, center_Lat, center_Lon, zoom, patch_size)

    output_path = patch_output_path(patch_save_root, center_Lat, center_Lon)
    patch.save(output_path)

    print("Patch saved:", output_path)
    print("Final image shape:", patch.size)
    print("Lasted a total of {:.2f} seconds".format(time.time() - start_time))
    return output_path


if __name__ == "__main__":
    get_patch_from_GM(47.535714, -52.752814, 18)
