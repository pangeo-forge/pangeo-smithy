from prefect import task, Flow

import pandas as pd
import os
import fsspec
import zarr


def src_url_from_key(key):
    source_url_pattern = 'https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/v2.1/access/avhrr/{yyyymm}/oisst-avhrr-v02r01.{yyyymmdd}.nc'
    return source_url_pattern.format(yyyymm=key.strftime('%Y%m'), yyyymmdd=key.strftime('%Y%m%d'))
    
cache_location = 'gs://pangeo-scratch/rabernat/pangeo_smithy/oisst-avhrr-v02r01-cache/'
    
    
@task
def download(key):
    source_url = src_url_from_key(key)
    os.path.join(cache_location, str(hash(key)))
    target_url = os.path.join(cache_location, str(hash(key)))
    
    # there is probably a better way to do caching!
    try:
        fsspec.open(target_url).open()
        return target_url
    except FileNotFoundError:
        pass
    
    with fsspec.open(source_url, mode='rb') as source:
        with fsspec.open(target_url, mode='wb') as target:
            target.write(source.read())
    return target_url


@task
def combine_and_publish(sources, target):
    import xarray as xr
    # couldn't figure out how to do this with fsspec and open_mfdataset
    dsets = []
    double_open_files = [fsspec.open(url).open() for url in sources]
    ds = xr.open_mfdataset(double_open_files, combine='nested', concat_dim='time')

    mapper = fsspec.get_mapper(target)
    ds.to_zarr(mapper)
    zarr.consolidate_metadata(mapper)
    
keys = pd.date_range('1981-09-01', '1981-09-06', freq='D')

with Flow("Pangeo-Forge") as flow:
    sources = [download(k) for k in keys]
    target_path = 'gs://pangeo-scratch/rabernat/pangeo_smithy/oisst-avhrr-v02r01-target/'
    combine_and_publish(sources, target_path)
    
flow.run()