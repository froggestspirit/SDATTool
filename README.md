# SDATTool
By FroggestSpirit

Unpack/Pack NDS SDAT Files

Make backups, this can overwrite files without confirmation

Usage: python3 SDATTool [SDAT File] [mode] [SDAT Folder] [flags]

When building, if there are converted files present, they will be attempted to be built back into the respective format (overwriting any existing ones) Example: SDAT/SBNK/Bank.json would be built into SDAT/SBNK/Bank.sbnk, overwriting any existing version of it

Running SDATTool without a mode or file will attempt to run in GUI mode, which requires tkinter

Modes: 

      -u Unpack SDAT

      -b Build SDAT

      -e Extract SDAT from rom

      -c Convert dumped files (if not used, files will only be dumped)

New in version 2.0.5:

-Initial GUI support

New in version 2.0.4:

-SBNK entries get their own json files, removing duplicates

New in version 2.0.3:

-Parse and rebuild SBNK and SWAR files

New in version 2.0.2:

-Extract SDAT files from NDS rom

New in version 2.0.1:

-Building SDAT

-Unpack cleanup

New in version 2.0.0:

-Complete rewrite