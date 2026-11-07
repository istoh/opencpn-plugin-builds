#!/usr/bin/env python3
"""Make an OpenCPN MBTiles overlay of satellite imagery over land only.

Water stays transparent, so the nautical chart shows at sea and the imagery
on land. OpenCPN draws MBTiles with type=overlay on top of the other charts,
one zoom level at a time, so every zoom level from --zoom is generated.

Runs inside the GDAL container started by tools/land-overlay.sh.
"""

import argparse
import math
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import zipfile

from osgeo import gdal, ogr

gdal.UseExceptions()
CACHE = Path("/cache")
EARTH = 20037508.342789244
AGENT = "opencpn-plugin-builds land-overlay (+https://github.com/istoh/opencpn-plugin-builds)"
# OpenStreetMap land polygons: accurate coastlines, ODbL.
OSM_LAND = "https://osmdata.openstreetmap.de/download/land-polygons-split-4326.zip"
SOURCES = {
    # Sentinel-2 cloudless by EOX: 10 m imagery, sharp to about zoom 14.
    # 2016 is CC BY 4.0; later years are CC BY-NC-SA 4.0 (non-commercial).
    "eox": ("https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2025_3857/default/GoogleMapsCompatible/"
            "${z}/${y}/${x}.jpg",
            "Sentinel-2 cloudless - https://s2maps.eu by EOX IT Services GmbH "
            "(Contains modified Copernicus Sentinel data 2025), CC BY-NC-SA 4.0"),
}
# ESA WorldCover 10 m land cover (CC BY 4.0): class 80 is permanent water. Read
# directly from the cloud-optimized GeoTIFFs, one per 3x3 degree cell.
WORLDCOVER = ("/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
              "ESA_WorldCover_10m_2021_v200_{cell}_Map.tif")
WATER = 80
MAX_TILES = 20000


def worldcover_cells(west, south, east, north):
    for lat in range(math.floor(south / 3) * 3, math.ceil(north / 3) * 3, 3):
        for lon in range(math.floor(west / 3) * 3, math.ceil(east / 3) * 3, 3):
            yield f"{'N' if lat >= 0 else 'S'}{abs(lat):02d}{'E' if lon >= 0 else 'W'}{abs(lon):03d}"


def georeference(grid):
    x0, y0, x1, y1 = grid["outputBounds"]
    return (f'<SRS>EPSG:3857</SRS><GeoTransform>{x0}, {(x1 - x0) / grid["width"]}, 0, '
            f'{y1}, 0, {-(y1 - y0) / grid["height"]}</GeoTransform>')


def worldcover_alpha(bounds, grid, scratch):
    """A Byte raster on the output grid: 0 on water or outside WorldCover (open sea), 255 on land."""
    sources = []
    for cell in worldcover_cells(*bounds):
        try:
            gdal.Open(WORLDCOVER.format(cell=cell))
            sources.append(WORLDCOVER.format(cell=cell))
        except RuntimeError:
            pass  # no land in this cell
    classes = scratch / "worldcover.tif"
    if sources:
        mosaic = gdal.BuildVRT(str(scratch / "worldcover.vrt"), sources)
        mosaic = None
        warped = gdal.Warp(str(classes), str(scratch / "worldcover.vrt"), resampleAlg="near", **grid,
                           creationOptions=["TILED=YES", "COMPRESS=DEFLATE"])
        warped = None
    alpha = scratch / "alpha.vrt"
    width, height = grid["width"], grid["height"]
    # Linear LUT between integer points: 0 (no data) and 80 (water) map to 0, the rest to 255.
    source = (f'<ComplexSource><SourceFilename relativeToVRT="0">{classes}</SourceFilename>'
              f'<SourceBand>1</SourceBand><LUT>0:0,1:255,{WATER - 1}:255,{WATER}:0,{WATER + 1}:255,255:255</LUT>'
              f'</ComplexSource>') if sources else ""
    alpha.write_text(f'<VRTDataset rasterXSize="{width}" rasterYSize="{height}">{georeference(grid)}'
                     f'<VRTRasterBand dataType="Byte" band="1">{source}</VRTRasterBand></VRTDataset>')
    return alpha, bool(sources)


def download(url, destination):
    if destination.is_file():
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}", flush=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    with urlopen(Request(url, headers={"User-Agent": AGENT}), timeout=120) as response, \
            partial.open("wb") as output:
        shutil.copyfileobj(response, output, 1 << 20)
    partial.replace(destination)
    return destination


def land_source(spec):
    """A path to an OGR land-polygon dataset, downloading and unpacking a zip when needed."""
    if not spec.startswith(("http://", "https://")):
        return spec
    archive = download(spec, CACHE / "land" / Path(urlsplit(spec).path).name)
    unpacked = archive.with_suffix("")
    if not unpacked.is_dir():
        print(f"Unpacking {archive.name}", flush=True)
        with zipfile.ZipFile(archive) as zipped:
            zipped.extractall(unpacked.with_suffix(".part"))
        unpacked.with_suffix(".part").replace(unpacked)
    shapes = sorted(unpacked.rglob("*.shp"))
    if not shapes:
        raise SystemExit(f"No shapefile in {archive}")
    return str(shapes[0])


def mercator(lon, lat):
    lat = max(min(lat, 85.0511), -85.0511)
    return lon * EARTH / 180, math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * EARTH / math.pi


def wms_xml(template, max_zoom, path):
    url = template.replace("{z}", "${z}").replace("{x}", "${x}").replace("{y}", "${y}").replace("$${", "${")
    path.write_text(f"""<GDAL_WMS>
  <Service name="TMS"><ServerUrl>{url.replace('&', '&amp;')}</ServerUrl></Service>
  <DataWindow>
    <UpperLeftX>{-EARTH}</UpperLeftX><UpperLeftY>{EARTH}</UpperLeftY>
    <LowerRightX>{EARTH}</LowerRightX><LowerRightY>{-EARTH}</LowerRightY>
    <TileLevel>{max_zoom}</TileLevel><TileCountX>1</TileCountX><TileCountY>1</TileCountY>
    <YOrigin>top</YOrigin>
  </DataWindow>
  <Projection>EPSG:3857</Projection>
  <BlockSizeX>256</BlockSizeX><BlockSizeY>256</BlockSizeY><BandsCount>3</BandsCount>
  <MaxConnections>4</MaxConnections>
  <UserAgent>{AGENT}</UserAgent>
  <Cache><Path>{CACHE / 'tiles'}</Path></Cache>
</GDAL_WMS>
""")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bbox", required=True, help="west,south,east,north in degrees")
    parser.add_argument("--zoom", default="8-14", help="zoom levels, MIN-MAX (default 8-14)")
    parser.add_argument("--source", default="eox", help=f"{', '.join(SOURCES)} or an XYZ URL with {{z}}/{{x}}/{{y}}")
    parser.add_argument("--attribution", default="", help="attribution for a custom --source")
    parser.add_argument("--land", help="mask with land polygons (a file, a zip URL, or 'osm' for the "
                        "OpenStreetMap land polygons) instead of ESA WorldCover water")
    parser.add_argument("--name", default="Land overlay")
    parser.add_argument("--out", required=True, help="output .mbtiles")
    parser.add_argument("--yes", action="store_true", help=f"allow more than {MAX_TILES} tiles")
    args = parser.parse_args()

    west, south, east, north = map(float, args.bbox.split(","))
    if not (-180 <= west < east <= 180 and -85 <= south < north <= 85):
        parser.error("--bbox must be west,south,east,north with west < east and south < north")
    min_zoom, _, max_zoom = args.zoom.partition("-")
    min_zoom, max_zoom = int(min_zoom), int(max_zoom or min_zoom)
    if not 0 <= min_zoom <= max_zoom <= 18:
        parser.error("--zoom must be MIN-MAX between 0 and 18")
    template, attribution = SOURCES.get(args.source, (args.source, args.attribution))
    if "{z}" not in template.replace("${", "{"):
        parser.error("--source must be a known name or an XYZ URL with {z}, {x} and {y}")
    if args.land == "osm":
        args.land = OSM_LAND
    mask_credit = ("Land polygons © OpenStreetMap contributors (ODbL)" if args.land == OSM_LAND
                   else "" if args.land else "Water mask: ESA WorldCover 2021, CC BY 4.0")
    attribution = "; ".join(filter(None, [attribution, mask_credit]))

    # Snap the area to the tile grid of the most detailed zoom level.
    size = 2 * EARTH / 2 ** max_zoom
    x0, y0 = mercator(west, south)
    x1, y1 = mercator(east, north)
    x0, x1 = math.floor((x0 + EARTH) / size) * size - EARTH, math.ceil((x1 + EARTH) / size) * size - EARTH
    y0, y1 = math.floor((y0 + EARTH) / size) * size - EARTH, math.ceil((y1 + EARTH) / size) * size - EARTH
    tiles = sum(round((x1 - x0) / size / 2 ** level) * round((y1 - y0) / size / 2 ** level) or 1
                for level in range(max_zoom - min_zoom + 1))
    print(f"About {tiles} tiles, zoom {min_zoom}-{max_zoom}", flush=True)
    if tiles > MAX_TILES and not args.yes:
        raise SystemExit(f"More than {MAX_TILES} tiles. Use a smaller area or zoom range, or --yes.")

    output = Path(args.out)
    with tempfile.TemporaryDirectory() as scratch:
        scratch = Path(scratch)
        source = scratch / "source.xml"
        wms_xml(template, max_zoom, source)
        width, height = round((x1 - x0) / (size / 256)), round((y1 - y0) / (size / 256))
        grid = dict(dstSRS="EPSG:3857", outputBounds=(x0, y0, x1, y1), width=width, height=height,
                    multithread=True, warpOptions=["NUM_THREADS=ALL_CPUS"])
        masked = scratch / "masked.vrt"
        if args.land:
            print("Clipping land polygons", flush=True)
            margin = 0.05
            area = (west - margin, south - margin, east + margin, north + margin)
            land = scratch / "land.gpkg"
            clipped = gdal.VectorTranslate(str(land), land_source(args.land), format="GPKG", dstSRS="EPSG:4326",
                                           spatFilter=area, clipSrc=area, layerName="land",
                                           geometryType="MULTIPOLYGON")
            clipped = None  # flush to disk
            polygons = ogr.Open(str(land))
            if not polygons.GetLayer(0).GetFeatureCount():
                raise SystemExit("No land in this area.")
            polygons = None
            print("Fetching imagery and masking water", flush=True)
            masked = scratch / "masked.tif"
            warped = gdal.Warp(str(masked), str(source), cutlineDSName=str(land), dstAlpha=True,
                               resampleAlg="bilinear", **grid,
                               creationOptions=["TILED=YES", "COMPRESS=DEFLATE", "BIGTIFF=IF_SAFER"])
            warped = None
        else:
            print("Reading the ESA WorldCover water mask", flush=True)
            alpha, any_land = worldcover_alpha((west, south, east, north), grid, scratch)
            if not any_land:
                raise SystemExit("No land in this area.")
            print("Fetching imagery", flush=True)
            rgb = scratch / "rgb.tif"
            warped = gdal.Warp(str(rgb), str(source), resampleAlg="bilinear", **grid,
                               creationOptions=["TILED=YES", "COMPRESS=DEFLATE", "BIGTIFF=IF_SAFER"])
            warped = None
            # The imagery's RGB bands plus the mask as alpha.
            bands = [(rgb, 1, "Red"), (rgb, 2, "Green"), (rgb, 3, "Blue"), (alpha, 1, "Alpha")]
            masked.write_text(f'<VRTDataset rasterXSize="{width}" rasterYSize="{height}">{georeference(grid)}' + "".join(
                f'<VRTRasterBand dataType="Byte" band="{index}"><ColorInterp>{color}</ColorInterp>'
                f'<SimpleSource><SourceFilename relativeToVRT="0">{path}</SourceFilename>'
                f'<SourceBand>{band}</SourceBand></SimpleSource></VRTRasterBand>'
                for index, (path, band, color) in enumerate(bands, 1)) + "</VRTDataset>")

        print("Writing MBTiles", flush=True)
        if output.exists():
            output.unlink()
        tiles_out = gdal.Translate(str(output), str(masked), format="MBTILES",
                       creationOptions=["TILE_FORMAT=PNG", "TYPE=overlay", f"NAME={args.name}",
                                        f"DESCRIPTION=Satellite imagery over land, zoom {min_zoom}-{max_zoom}"])
        tiles_out = None
        dataset = gdal.Open(str(output), gdal.GA_Update)
        if max_zoom > min_zoom:
            print("Building lower zoom levels", flush=True)
            dataset.BuildOverviews("AVERAGE", [2 ** level for level in range(1, max_zoom - min_zoom + 1)])
        dataset = None

    with sqlite3.connect(output) as db:
        db.execute("DELETE FROM metadata WHERE name IN ('attribution', 'minzoom', 'maxzoom', 'type')")
        db.executemany("INSERT INTO metadata (name, value) VALUES (?, ?)", [
            ("attribution", attribution), ("type", "overlay"),
            ("minzoom", str(db.execute("SELECT MIN(zoom_level) FROM tiles").fetchone()[0])),
            ("maxzoom", str(db.execute("SELECT MAX(zoom_level) FROM tiles").fetchone()[0])),
        ])
        count, levels = db.execute("SELECT COUNT(*), GROUP_CONCAT(DISTINCT zoom_level) FROM tiles").fetchone()
    print(f"{output}: {count} tiles, zoom levels {levels}, {output.stat().st_size / 2**20:.1f} MiB")
    print(f"Attribution: {attribution}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
