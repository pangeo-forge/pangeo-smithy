# Pangeo Forge

The idea of Pangeo Forge is to copy the very successful pattern of Conda Forge
for crowdsourcing the curation of an analysis-ready data library.

In Conda Forge, a maintainer contributes a recipe which is used to generate a
conda package from a source code tarball. Behind the scenes, CI downloads the
source code, builds the package, and uploads it to a repository.

In Pangeo Forge, a maintainer contributes a recipe which is used to generate
an analysis-ready cloud-based copy of a dataset in a cloud-optimized format
like Zarr. Behind the scenes, CI downloads the original files from their
source (e.g. FTP, HTTP, or OpenDAP), combines them using xarray, writes out
the Zarr file, and uploads to cloud storage.

There are many details to work out. It is useful to think about what ingredients
might go into a recipe.

Sample `meta.yaml` recipe.

```yaml

dataset:
  # should be a unique name and valid python identifier
  name: noaa_oisst_avhrr_only
  # how should we version datasets?
  version: 0.1.0

# where do we find the files
source:
  format: netcdf
  # example: https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/access/avhrr-only/198109/avhrr-only-v2.19810901.nc
  url_pattern: https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/access/avhrr-only/{{ yyyymm }}/avhrr-only-v2.{{ yyyymmdd }}.nc
  # mirror pandas syntax
  # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.date_range.html
  date_range:
    start: 1981-09-01
    # the end date can
    end: 2019-08-11
    freq: D

# tell xarray how to open and combine the files
combine:
  # options passed to xarray.open_dataset
  open_options:
    decode_cf: False
  combine_method: combine_by_coords
  # options passed to combine method
  combine_options:
    compat: no_conflicts

# where / how to save the data
output:
  format: zarr
  chunks:
    time: 5
  consolidated: True
  target:
    urlpath: gcs://pangeo-noaa/
    # how to deal with credentials?
    credentials: ???

about:
  home: https://www.ncdc.noaa.gov/oisst
  # how to deal with licensing?
  license: ???
  summary: 'NOAA Optimally Interpolated Sea Surface Temperature (AVHRR Only)'
  description: |
    The NOAA 1/4° daily Optimum Interpolation Sea Surface Temperature (or daily OISST) is an analysis constructed by combining observations from different platforms (satellites, ships, buoys) on a regular global grid. A spatially complete SST map is produced by interpolating to fill in gaps.
    The methodology includes bias adjustment of satellite and ship observations (referenced to buoys) to compensate for platform differences and sensor biases. This proved critical during the Mt. Pinatubo eruption in 1991, when the widespread presence of volcanic aerosols resulted in infrared satellite temperatures that were much cooler than actual ocean temperatures (Reynolds 1993).
  support_email: oisst-help@noaa.gov
```
