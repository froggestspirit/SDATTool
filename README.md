# SDATTool
By FroggestSpirit

Unpack/Pack NDS SDAT Files

Make backups, this can overwrite files without confirmation

Usage: python3 SDATTool.py [SDAT File] [mode] [SDAT Folder] [flags]

Modes: 

      -b Build SDAT

      -u Unpack SDAT

Flags:
      
      -ns Build without a SymbBlock
      
If only a SDAT file is provided, the output directory will be the same as the SDAT, with a new folder created. This will unpack to that folder. Similarly, the SDAT can be rebuilt from the same folder name if only the SDAT filename is provided with mode -b

Un-edited rebuilt SDAT files should be 1:1, if an SDAT is ripped from a game, decompiled and rebuilt, without being 1:1, please let me know.


New in version 1.0.0:

-Code overhull and JSON formatting

-Temporarily removed options to optimize SDAT (They will be the next priority)

-Fixed SSEQ dumping