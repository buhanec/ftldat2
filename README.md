# ftldat2

A Python 2/3 tool for unpacking and packing FTL .dat files. Inspired by [bwesterb/ftldat](https://github.com/bwesterb/ftldat).
 
## Installation

    pip install git+ssh://git@github.com/buhanec/ftldat2

## Usage

    ftldat2 <input> [output]
    
If input is an unpacked directory, it will pack it into same named .dat file or specified output file.

If input is a packed file, it will be unpacked into same named directory or specified directory.