# SDATTool
By FroggestSpirit Version 0.8.0

Unpack/Pack NDS SDAT Files

Make backups, this can overwrite files without confirmation

Usage: python3 SDATTool.py [SDAT File] [mode] [SDAT Folder] [flags]

Modes: 

      -b Build SDAT

      -u Unpack SDAT
      
      -h Show help

Flags:

      -m Calculate MD5 for unpacked files
      
      -o Build Optimized (removes duplicate files by comparing MD5)
      
      -ru Build without unused entries (can break games)
      
      -ns Build without a SymbBlock
      
If only a SDAT file is provided, the output directory will be the same as the SDAT, with a new folder created. This will unpack to that folder. Similarly, the SDAT can be rebuilt from the same folder name if only the SDAT filename is provided with mode -b

Un-edited rebuilt SDAT files should be 1:1, if an SDAT is ripped from a game, decompiled and rebuilt, without being 1:1, please let me know.

Un-edited rebuilt SDAT files using the -o flag should work normally in-game, if not please let me know.


New in version 0.8.0:

-SWAR files now unpack in their own directory as SWAVs. Building will look for a built SWAR first, then if not found, build the SWAR from the SWAVs

