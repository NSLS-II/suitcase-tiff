# suitcase.tiff

This is a suitcase subpackage for reading a particular file format.

## Installation

```
pip install suitcase-tiff
```

## Quick Start

`suitcase-tiff` supports stack and series methods.

Using stack:

```
import suitcase.tiff_stack
docs = db[-1].documents(fill=True)
suitcase.tiff_stack.export(docs, 'my_exported_files/')
```

The exported file will have path:
`my_exported_files/c416e70a-eb99-4964-bfc0-64e291313cce-primary-spot_img.tiff`

Using series:

```
import suitcase.tiff_series
docs = db[-1].documents(fill=True)
suitcase.tiff_series.export(docs, 'my_exported_files/')
```
Instead of one file, the exportor create seperate file per row:
```
my_exported_files/c416e70a-eb99-4964-bfc0-64e291313cce-primary-spot_img-0.tiff
my_exported_files/c416e70a-eb99-4964-bfc0-64e291313cce-primary-spot_img-1.tiff
my_exported_files/c416e70a-eb99-4964-bfc0-64e291313cce-primary-spot_img-2.tiff
my_exported_files/c416e70a-eb99-4964-bfc0-64e291313cce-primary-spot_img-3.tiff
...

```

The file prefix `c416e70a-eb99-4964-bfc0-64e291313cce` is the unique ID of the
run. The default file prefix can be changed with the `file_prefix` keyword
argument. See the documentation link below.

## Documentation

See the [suitcase documentation](https://blueskyproject.io/suitcase/).
