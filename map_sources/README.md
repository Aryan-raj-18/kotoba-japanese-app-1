# Offline Japan Explorer geography

Kotoba's map is drawn from geographic data, with all capital pins and map
layers sharing a Mercator projection. Coastlines are simplified for display.
Train journeys connect learning stops and are not exact railway alignments.

## Prefectures

`japan-prefectures.geojson` is the simplified JPN ADM1 dataset from
geoBoundaries, boundary ID JPN-ADM1-47310658, representing 2017 boundaries.
Source: OpenStreetMap / Wambacher. The dataset contains 47 prefectures.

- Dataset: https://www.geoboundaries.org/api/current/gbOpen/JPN/ADM1/
- Pinned source: https://github.com/wmgeolab/geoBoundaries/blob/9469f09/releaseData/gbOpen/JPN/ADM1/geoBoundaries-JPN-ADM1_simplified.geojson
- Copyright: © OpenStreetMap contributors; https://www.openstreetmap.org/copyright
- Licence: Open Data Commons Open Database License 1.0.
  https://opendatacommons.org/licenses/odbl/1-0/

The source database is included here. The geographic path data derived from
it in `static/js/japan_geography.js` is also available under ODbL 1.0.
Changes: clipping to the map extent and conversion to projected SVG paths.
The application's code and learning content are separate from this database.

## Surrounding land

`natural-earth-land.geojson` is Natural Earth's 1:50m land geometry.
Natural Earth data is public domain.

- Source: https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_50m_land.geojson
- Terms: https://www.naturalearthdata.com/about/terms-of-use/

## Rebuild

Install `shapely==2.1.2` in a Python environment, then run
`python build_japan_map.py` and `python sync_android.py` from the project root.
The app uses the generated, bundled JavaScript and requires no map service,
external tiles, API key, or runtime geometry dependency.
