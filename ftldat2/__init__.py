#!/usr/bin/env python

"""FTL data file interface."""

from __future__ import print_function
import struct
import os
import glob
import sys

__author__ = 'buhanec'
__version__ = '0.1.dev.0'
__all__ = ('FTLPack', 'FTLPackError')


def sizeof(num: int):
    """
    Nicely format file size.

    :param num: File size in bits.
    :return: Formatted size in bytes.
    """
    if abs(num) < 1024:
        return '{}B'.format(num)
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024:
            return '{:3.1f}{}B'.format(num, unit)
        num /= 1024
    return '{:.1f}YiB'.format(num)


class FTLPackError(Exception):
    """Generic error for FTL (un)packing."""


class FileEntry:
    """File entry in FTL data file."""

    def __init__(self, path: str, contents: bytes):
        """
        Initialise `FileEntry`.

        :param path: Path to file.
        :param contents: Contents of file.
        """
        self.path = path
        self.contents = contents

    @property
    def size(self) -> int:
        """
        Calculate size of entry.

        Total size is 4 bits for path length, 4 bits for content
        length, the length of the path and the length of the content.

        :return: Entry size.
        """
        return 8 + len(self.path) + len(self.contents)

    def __repr__(self) -> str:
        return '<FileEntry: {} ({})>'.format(self.path, sizeof(self.size))


class FTLPack:
    """Abstracted representation of a FTL data file."""

    def __init__(self, path: str=None):
        """
        Initialise `FTLPack`.

        If `path` is a file, will attempt to load as if `path` is FTL
        compressed data file. If `path` is a directory, will attempt to
        load as if `path` is a source of data entries.

        :param path: Compressed or uncompressed entries.
        """
        self.index = []
        self.index_size = 0
        if path is not None:
            if os.path.islink(path):
                path = os.readlink(path)
            if os.path.isfile(path):
                self.load(path)
            elif os.path.isdir(path):
                self.construct(path)

    def load(self, filename: str):
        """
        Populate entries from compressed FTL data files in path.

        :param filename: File to read entries from.
        """
        self.index = []
        with open(filename, 'rb') as f:
            self.index_size = struct.unpack('<L', f.read(4))[0]
            for index_offset in range(4, 4 + 4 * self.index_size, 4):
                f.seek(index_offset)
                offset = struct.unpack('<L', f.read(4))[0]
                if offset > 0:
                    f.seek(offset)
                    size, path_len = struct.unpack('<LL', f.read(8))
                    self.index.append(FileEntry(
                        path=f.read(path_len).decode(),
                        contents=f.read(size)
                    ))
            f.seek(4 + 4 * self.index_size)

    def save(self, filename: str):
        """
        Write entries in compressed FTL data form to path.

        :param filename: File to write entries to.
        """
        if len(self.index) > self.index_size:
            raise FTLPackError('Index ({}) too small for {} entries.'
                               .format(len(self.index), self.index_size))
        with open(filename, 'wb') as f:
            f.write(struct.pack('<L', self.index_size))
            offset = 4 + 4 * self.index_size
            for entry in self.index:
                f.write(struct.pack('<L', offset))
                offset += entry.size
            f.write(b'\x00' * 4 * (self.index_size - len(self.index)))
            for entry in self.index:
                f.write(struct.pack('<LL', len(entry.contents),
                                    len(entry.path)))
                f.write(entry.path.encode())
                f.write(entry.contents)

    def construct(self, path: str, min_index=2048):
        """
        Populate entries from non-compressed files in path.

        Index size will be the smaller of `min_index` and the actual
        required size of the index.

        :param path: Path to read entries from.
        :param min_index: Minimum index size.
        """
        self.index = []
        clip = len(path) + len(os.path.sep)
        for path in glob.iglob(os.path.join(path, '**'), recursive=True):
            if os.path.islink(path):
                path = os.readlink(path)
            if not os.path.isfile(path):
                continue
            with open(path, 'rb') as f:
                self.index.append(FileEntry(
                    path=path[clip:].replace(os.path.sep, '/'),
                    contents=f.read()
                ))
        self.index_size = max(len(self.index), min_index)

    def destruct(self, path: str):
        """
        Write entries in non-compressed form to path.

        :param path: Path to write entries to.
        """
        for entry in self.index:
            target = os.path.join(path, entry.path.replace('/', os.path.sep))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, 'wb') as f:
                f.write(entry.contents)


def main():
    """Entry point for CLI command."""
    source = sys.argv[1]
    pack = FTLPack()
    if os.path.islink(source):
        source = os.readlink(source)
    if os.path.isfile(source):
        pack.load(filename=source)
        packed_source = True
    else:
        pack.construct(path=source)
        packed_source = False
    try:
        target = sys.argv[2]
    except IndexError:
        if packed_source:
            target = '.'
        else:
            base = os.path.basename(source)
            if not base:
                base = os.path.dirname(source)
            target = '{}.dat'.format(base)
    if packed_source:
        pack.destruct(path=target)
    else:
        pack.save(filename=target)
