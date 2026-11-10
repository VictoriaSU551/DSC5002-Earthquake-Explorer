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

The public annual/regional extension also includes an offline aggregate-only HTML tool with the same embedded Plotly runtime and retained MIT license header. The original-code MIT license does not replace third-party terms.

## Integrated poster and animation (2026-11-10)

The published animation embeds only 1,044 public USGS observations from the
three specified case windows, plus the attributed boundary/coastline geometry
and the Plotly runtime (license header retained). Full source CSVs and submitted
team archives remain local. Poster PDFs embed subsets of Arial (Windows authoring)
and DejaVu Sans (Matplotlib). Optional PDF dependencies are listed separately in
requirements-poster.txt. RQ3 section code was adapted from Member 3; magnitude
code from HUANG Youkun; the animation from the supplied RQ5 contribution.

CityU Language Centre's poster and script pages are design references, linked in
docs/TEAM_REVIEW.md. Their sample poster image is not redistributed in this repo.
