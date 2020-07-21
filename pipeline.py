from prefect import task, Flow

import pandas as pd
import os
import fsspec
import zarr
import itertools

# https://alexwlchan.net/2018/12/iterating-in-fixed-size-chunks/
def chunked_iterable(iterable, size):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk

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
def combine_and_write(sources, target, append_dim, first=True):
    import xarray as xr
    # couldn't figure out how to do this with fsspec and open_mfdataset
    dsets = []
    double_open_files = [fsspec.open(url).open() for url in sources]
    ds = xr.open_mfdataset(double_open_files, combine='nested', concat_dim=concat_dim)
 
    if first:
        kwargs = dict(mode='w')
    else:
        kwargs = dict(mode='a', append_dim=append_dim)
    
    mapper = fsspec.get_mapper(target)
    ds.to_zarr(mapper, **kwargs)
    
@task
def consolidate_metadata(target):
    mapper = fsspec.get_mapper(target)
    zarr.consolidate_metadata(mapper)


keys = pd.date_range('1981-09-01', '1981-09-10', freq='D')
target_path = 'gs://pangeo-scratch/rabernat/pangeo_smithy/oisst-avhrr-v02r01-target/'
concat_dim = 'time'
files_per_chunk = 5

with Flow("Pangeo-Forge") as flow:
    sources = [download(k) for k in keys]
    first = True
    write_tasks = []
    for source_group in chunked_iterable(sources, files_per_chunk):
        write_task = combine_and_write(source_group, target_path, concat_dim, first=first)
        write_tasks.append(write_task)
        first = False
    cm = consolidate_metadata(target_path)

# create dependencies in imperative mode
for n in range(1, len(write_tasks)):
    write_tasks[n].set_upstream(write_tasks[n-1], flow=flow)
cm.set_upstream(write_tasks[-1], flow=flow)


### DO IT! ###
flow.run()