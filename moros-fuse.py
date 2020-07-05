#!/usr/bin/env python

import logging

from stat import S_IFDIR, S_IFREG
from errno import ENOENT
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
from textwrap import wrap

class MorosFuse(LoggingMixIn, Operations):
    chmod = None
    chown = None
    create = None
    mkdir = None
    readlink = None
    rename = None
    rmdir = None
    symlink = None
    truncate = None
    unlink = None
    utimens = None
    write = None

    def __init__(self, image):
        self.image = open(image, "rb")
        addr = 2048 * 512
        self.image.seek(addr)
        block = self.image.read(512)

    def destroy(self, path):
        self.image.close()
        return

    def getattr(self, path, fh=None):
        (kind, addr, size, name) = self.__scan(path)
        if addr == 0:
            raise FuseOSError(ENOENT)
        mode = S_IFDIR | 0o755 if kind == 0 else S_IFREG | 0o644
        return { "st_atime": 0, "st_mtime": 0, "st_uid": 0, "st_gid": 0, "st_mode": mode, "st_size": size }

    def read(self, path, size, offset, fh):
        (kind, next_block_addr, size, name) = self.__scan(path)
        res = b""
        while next_block_addr != 0:
            self.image.seek(next_block_addr)
            next_block_addr = int.from_bytes(self.image.read(4), "big") * 512
            if offset < 512 - 4:
                buf = self.image.read(min(512 - 4, size))
                res = b"".join([res, buf[offset:]])
                offset = 0
            else:
                offset -= 512 - 4
            size -= 512 - 4
        return res

    def readdir(self, path, fh):
        (_, next_block_addr, _, _) = self.__scan(path)
        files = [".", ".."]
        while next_block_addr != 0:
            self.image.seek(next_block_addr)
            next_block_addr = int.from_bytes(self.image.read(4), "big")
            offset = 4
            while offset < 512:
                kind = int.from_bytes(self.image.read(1), "big")
                addr = int.from_bytes(self.image.read(4), "big") * 512
                if addr == 0:
                    break
                size = int.from_bytes(self.image.read(4), "big")
                n = int.from_bytes(self.image.read(1), "big")
                name = self.image.read(n).decode("utf-8")
                files.append(name)
                offset += 1 + 4 + 4 + 1 + n
        return files

    def __scan(self, path):
        dirs = path[1:].split("/")
        d = dirs.pop(0)
        next_block_addr = (2048 + 2 + 512) * 512
        if d == "":
            return (0, next_block_addr, 0, d)
        while next_block_addr != 0:
            self.image.seek(next_block_addr)
            next_block_addr = int.from_bytes(self.image.read(4), "big")
            offset = 4
            while offset < 512:
                kind = int.from_bytes(self.image.read(1), "big")
                addr = int.from_bytes(self.image.read(4), "big") * 512
                if addr == 0:
                    break
                size = int.from_bytes(self.image.read(4), "big")
                n = int.from_bytes(self.image.read(1), "big")
                name = self.image.read(n).decode("utf-8")
                if name == d:
                    if len(dirs) == 0:
                        return (kind, addr, size, name)
                    else:
                        next_block_addr = addr
                        d = dirs.pop(0)
                    break
                offset += 1 + 4 + 4 + 1 + n
        return (0, 0, 0, "")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('image')
    parser.add_argument('mount')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    fuse = FUSE(MorosFuse(args.image), args.mount, ro=True, foreground=True, allow_other=True)
