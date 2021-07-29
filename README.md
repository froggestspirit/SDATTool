# SDATTool
By FroggestSpirit

Unpack/Pack NDS SDAT Files

Make backups, this can overwrite files without confirmation

Usage: python3 SDATTool [SDAT File] [mode] [SDAT Folder] [flags]

Modes: 

      -b Build SDAT

      -u Unpack SDAT

Flags:
      
      -ns Build without a SymbBlock

      -o Optimize, remove duplicate files, and unused files

      -os Optimize for size, same as above, but remove bank entries in the infoBlock (may break in game)

      -or Optimize for ram, try to minimize the size of files that need to be loaded for each song (testing, might be buggy)

      -wr Write raw, extract the raw files
      
If only a SDAT file is provided, the output directory will be the same as the SDAT, with a new folder created. This will unpack to that folder. Similarly, the SDAT can be rebuilt from the same folder name if only the SDAT filename is provided with mode -b

Un-edited rebuilt SDAT files should be 1:1, if an SDAT is ripped from a game, decompiled and rebuilt, without being 1:1, please let me know.

-o Optimize (not -os optimize size) is geared towards not breaking in-game compatibility. If this is used and doesn't work in-game the same as the original, please let me know

-or works by creating a copy of the sbnk and swars used by each sseq, and tries to only build them with the instruments used in the sseq, removing the rest. The file size is generally larger, but the size of the sbnk and swars that need to load with the sseq should hopefully be smaller. This will also write a lot more files to the unpack directory

To make better use of the -or option, first unpack a SDAT, then re-build it with -or. After, unpack that new SDAT, and rebuild that new one with -o


New in version 1.4.0:

-SSEQ files now convert to MIDI and back. This should be a 1:1 conversion, but was only tested on a couple SDAT files

New in version 1.3.0:

-Code cleanup/organization

-Raw files no longer extract by default. They can be extracted with the -wr flag

-SSEQ files are now properly parsed to txt, and compiled back

New in version 1.2.2:

-Optimize for RAM option now creates only one SWAR per sseq, even if it's bank normally uses more

New in version 1.2.1:

-Fixes for optimize for RAM option

New in version 1.2.0:

-Optimize for RAM option

New in version 1.1.0:

-Code cleanup

-Optimize and optimize size flags

New in version 1.0.0:

-Code overhull and JSON formatting

-Temporarily removed options to optimize SDAT (They will be the next priority)

-Fixed SSEQ dumping