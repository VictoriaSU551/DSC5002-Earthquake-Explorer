# Sources and third party terms

## USGS Earthquake Catalog

Source: https://earthquake.usgs.gov/fdsnws/event/1/

The analysis uses the preferred event values returned by this public service, including IDs and magnitude types. Cite the U.S. Geological Survey and retain the query provenance. No USGS endorsement is implied. The source CSVs are downloaded locally rather than distributed in this code repository.

## PB2002

Bird, P. (2003). An updated digital model of plate boundaries. *Geochemistry Geophysics Geosystems*, 4(3), 1027. https://doi.org/10.1029/2001GC000252

GeoJSON conversion: https://github.com/fraxen/tectonicplates

Credit **Hugo Ahlenius, Nordpil and Peter Bird**. The conversion repository uses the **Open Data Commons Attribution License 1.0 (ODC-By)**. Its pinned license text is downloaded with the geometry to `data/raw/geography/PB2002_LICENSE.md`. Generated maps and dashboard text retain source attribution. The code's MIT license does not replace the data license.

Pinned commit: `339b0c56563c118307b1f4542703047f5f698fae`.

## Natural Earth

Source: https://www.naturalearthdata.com/downloads/110m-physical-vectors/

Pinned GeoJSON mirror: https://github.com/nvkelso/natural-earth-vector at `ca96624a56bd078437bca8184e78163e5039ad19`.

Natural Earth coastline and land are public-domain cartographic data. They supply geographic context and the globe's sampled land mask, not earthquake observations.

## Runtime libraries

The project depends on the libraries listed in `requirements.txt`, which retain their upstream licenses. Plotly JavaScript is embedded from the installed Plotly Python package in the generated local HTML for offline use; its distributed license header is retained. It is not committed as a vendored JavaScript file. Matplotlib and DejaVu Sans render the local research figures.
