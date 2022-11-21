# PyNeoSD
Python NEO-SD image generator

For Neo-Geo homebrew, designed to drop into your makefile/build script to easily create a NEO-SD image for use in MiSTers and flash carts.

## Usage
`neosd.py file [file ...] --output OUT [-s] [METADATA_FIELDS]`

Pass PROM, MROM, CROM, SROM, and VROM images in by filename, they will be automatically sorted and placed into the proper sections.
`-o`/`--output` specifies the output NEO-SD image.

Example usage: `neosd 202-m1.m1 202-s1.s1 202-p1.p1 202-v1.v1 202-c1.c1 202-c2.c2 --output mygame.neo` for typical output from NGDevKit.

`-s`/`--silent` will silence all non-error output if you want the script to be quiet.

### Metadata Fields
All of these are optional, and are only really relevant if you're using a flash cart (or expect that others will be using a flash cart).

`--name "My Game Name"` specifies the game name that the flash cart will display. Maximum length is 32 characters, defaults to "Untitled".

`--company "MegaCorp"` specifies the name of the developer/publisher company. Maximum length is 16 characters, defaults to "None".

`--ngh 1` specifies the NGH number of your game, in decimal. I don't think flash carts use this since it's included in the PROM anyway, but it's included here for completeness's sake. You may prepend the argument with `0x` to use hexadecimal, to use BCD for instance. Defaults to 0.

`--genre Action` specifies the genre of your game, used for filtering. You must specify one of these 11 genres: "Action", "BeatEmUp", "Sports", "Driving", "Platformer", "Mahjong", "Shooter", "Quiz", "Fighting", "Puzzle", or "Other". Defaults to "Other".

`--year 2000` specifies the year your game was released, again used for filtering. Defaults to the current year.

## Known Issues
This is designed for homebrew only, and may fail on ROMs from official games.
Multiple PROMs are not properly supported, most notably.
