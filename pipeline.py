from prefect import task, Flow

import pandas as pd
import fsspec


url_pattern = 'https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/access/avhrr-only/{{ %Y%m }}/avhrr-only-v2.{{ %Y%m%d }}.nc'

date_range = {'start': '1981-09-01', 'end': '2019-08-11', 'freq': 'D'}
dates = pd.date_range(**date_range)
files = dates.strftime(url_pattern)


@task
def download(source):
    import wget

    wget.download(source)

    return target


@task
def combine(sources):
    import xarray as xr

    ds = xr.open_mfdataset(sources).chunk({'time': 5})
    
    return ds


@task
def publish(dataset, target):
    mapper = fsspec.get_mapper('gcs://pangeo-noaa/')
    dataset.to_zarr(mapper)


with Flow("Pangeo-Forge") as flow:
    sources = [download(f) for f in files]

    ds = combine(chunk)

    publish(ds, target_path)
