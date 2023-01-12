# k8s-image-upgrade-check  

A script to gather images in use and check for newer versions (Tags). 

## Setup
Clone the repo and cd into its root

Setup python environment
```bash
python3 -m venv k8s-image-upgrade-check
source ./k8s-image-upgrade-check/bin/activate
python3 -m pip install -r requirements.txt
```

## Use

See help for options:
```bash
python3 ./src/image_upgrade_check.py -h
```


### Filters
The updated tags output can be very long. Many registries have hundred (or even thousands) of tags, but most of those are not 'releases' and likely not a viable upgrade for most systems. Thus it is helpful to 'filter out the noise' so to speak.

`-T` allows you to filter out tags by regex (Exclusion filter).
- String must be wrapped in single quotes. 
- Multiple expressions can be used, separated by the pipe char `|` 
- Each expression must include start `^` and end `$` of line chars.


Example filter: 
- First part filters out hex string tags (eg commit hashs)
- The second part filters out the sha tags frequently seen on quay.io
```
'^[a-f0-9]{7,}.*$|^sha[0-9]*-[a-f0-9]+\.sig$`
```
