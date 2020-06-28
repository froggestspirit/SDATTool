# SDATTool
By FroggestSpirit Version 0.0.5

Unpack/Pack NDS SDAT Files

Make backups, this can overwrite files without confirmation

Usage: python3 SDATTool.py [SDAT File] [mode] [SDAT Folder] [flags]

Modes: 

      -b Build SDAT

      -u Unpack SDAT
      
      -h Show help

Flags:

      -m Calculate MD5 for unpacked files
      
      -o Build Optimized
      
      -ns tBuild without a SymbBlock
      
If only a SDAT file is provided, the output directory will be the same as the SDAT, with a new folder created. This will unpack to that folder. Similarly, the SDAT can be rebuilt from the same folder name if only the SDAT filename is provided with mode -b

Un-edited rebuilt SDAT files should be 1:1, if an SDAT is ripped from a game, decompiled and rebuilt, without being 1:1, please let me know.

New in version 0.0.5:

-Code is cleaned up more

New in version 0.0.4:

-InfoBlock.txt is the only necessary text file when building. FileID.txt can still be used to order the files for 1:1 building, otherwise only files defined in InfoBlock.txt will be used, in the order defined.

-SymbBlock.txt now only holds SeqArc names, so the sub-names can be defined. The master names will take the ID from the order defined in InfoBlock.txt. All other SymbBlock names are now pulled from InfoBlock.txt

-Since builds will now use symbols from InfoBlock.txt, -ns can be passed to build a SDAT without the symbBlock

-Flag for optimizing: pass flag -o, only files, banks, wavearcs, and players that are referenced in the InfoBlock.txt will be used in the build. The optimized flag will ignore the FileID.txt. Only the SEQ items will need to be removed, since any unreferenced banks, wavearcs or players will be excluded. combine with -ns for an even smaller SDAT filesize.

New in version 0.0.3:

-Reworked so files, banks and wavearcs are referenced by name in the infoBlock.txt file
