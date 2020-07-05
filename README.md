# MOROS-Fuse

This script can be used to mount in read-only a [MOROS](https://github.com/vinc/moros)
disk image on GNU/Linux.

## Usage

    pip install fusepy
    mkdir /tmp/moros
    git clone https://github.com/vinc/moros-fuse
    cd moros-fuse
    python moros-fuse.py ~/path/to/moros/disk.img /tmp/moros
