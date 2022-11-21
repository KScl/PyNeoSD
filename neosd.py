import argparse
import datetime
import re

version = 'v1.0'
license = '''Copyright (c) 2022 Kay Sinclaire.

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.
2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.
'''

# Fixed genre list for NEO-SD
genres = {
	"Action": 1, "BeatEmUp": 2, "Sports": 3, "Driving": 4, "Platformer": 5,
	"Mahjong": 6, "Shooter": 7, "Quiz": 8, "Fighting": 9, "Puzzle": 10,
	"Other": 0,
}

argp = argparse.ArgumentParser(usage="%(prog)s file [file ...] --output OUT [-s] [METADATA_FIELDS]",
	formatter_class=argparse.RawDescriptionHelpFormatter,
	add_help=False,
	description='''
PyNeoSD v1.0
Generate a NEO-SD packed ROM from given ROM images.''',
	epilog=f'''
Valid arguments to --genre are:  {str([opt for opt in genres.keys()])[1:-1]}

Copyright (c) 2022 Kay Sinclaire.
Released under the terms of the zlib License.
See --license for more details.

The most up to date version of this file can be found at
https://github.com/KScl/PyNeoSD/
''')

required = argp.add_argument_group('Required arguments')
optional = argp.add_argument_group('Optional arguments')
fields = argp.add_argument_group('NEO-SD metadata field arguments')

# Parse help and license first so they may do what they need to do without needing "required" args
# Remaining args are irrelevant because either they'll be the same as stdin, or we're exiting after anyway
optional.add_argument('-l', '--license', help="Print license info and exit", action="store_true")
optional.add_argument('-h', '--help', help="Print help and exit", action="store_true")
information_args, _ = argp.parse_known_args()

# Add other arguments now
required.add_argument('file', help="Input roms; type will be auto-detected by filename", nargs='+')
required.add_argument('-o', '--output', help="Output file name", required=True, metavar="OUT")

optional.add_argument('-s', '--silent', action="store_true", help="Silences non-error output")

fields.add_argument('--ngh', default=0, help="Set NGH number; prefix with 0x to use hexadecimal")
fields.add_argument('--name', default="Untitled", help="Set displayed game name (max length: 32)")
fields.add_argument('--company', default="None", help="Set manufacturer/company name (max length: 16)")
fields.add_argument('--genre', default="Other", help=f"Set displayed genre (see options below)", choices=genres, metavar="GENRE")
fields.add_argument('--year', default=datetime.date.today().year, help="Set displayed year of release")

if information_args.license:
	argp.exit(message=license)
if information_args.help:
	argp.exit(message=argp.format_help())

arguments = argp.parse_args()

if len(arguments.name) > 32:
	argp.error("argument --name: input too long (max 32)")
if len(arguments.company) > 16:
	argp.error("argument --company: input too long (max 16)")

# Gets length of all roms in a given list together
def combined_len(all_roms):
	length = 0
	for data in all_roms:
		length += len(data)
	return length

# Interleaves two roms together (used for CROMs)
def interleave(roma, romb):
	if len(roma) != len(romb):
		raise Exception("Odd/even CROM mismatch")
	tmp = [0] * (len(roma) + len(romb))
	tmp[::2] = roma
	tmp[1::2] = romb
	return bytes(tmp)

# -------------------------------------------------------------------
p_roms = []
s_roms = []
m_roms = []
v_roms = []
co_roms = []
ce_roms = []

# Match 1 for p_roms || p1 / p2 (program rom)
# Match 2 for s_roms || s1 (fix rom)
# Match 3 for m_roms || m1 (z80 rom)
# Match 4 for v_roms || v1 / v2 / v3 / v4 (ADPCM sample rom)
# Match 5 for co_roms || c1 / c3 / c5 / c7 (Sprite rom first bytes)
# Match 6 for ce_roms || c2 / c4 / c6 / c8 (Sprite rom second bytes)
rom_ptrn = re.compile("[-\.](?:(p[12])|(s1)|(m1)|(v[1234])|(c[1357])|(c[2468]))")
# -------------------------------------------------------------------

for file in arguments.file:
	mt = rom_ptrn.search(file)
	if mt is None:
		raise Exception("Don't know how to handle '%s'" % file)

	rom = open(file, 'rb')
	if mt.group(1):   p_roms.append(rom.read())
	elif mt.group(2): s_roms.append(rom.read())
	elif mt.group(3): m_roms.append(rom.read())
	elif mt.group(4): v_roms.append(rom.read())
	elif mt.group(5): co_roms.append(rom.read())
	elif mt.group(6): ce_roms.append(rom.read())

	if not arguments.silent:
		if mt.group(1):   print("added: %s (as type PROM)" % file)
		elif mt.group(2): print("added: %s (as type SROM)" % file)
		elif mt.group(3): print("added: %s (as type MROM)" % file)
		elif mt.group(4): print("added: %s (as type VROM)" % file)
		elif mt.group(5): print("added: %s (as type CROM-ODD)" % file)
		elif mt.group(6): print("added: %s (as type CROM-EVEN)" % file)

	rom.close()

# TODO:
# According to neosdconv, 2MB PROMs need to have the second MB first in the resulting NEO-SD file
# We do not currently handle this

if len(co_roms) != len(ce_roms) or combined_len(co_roms) != combined_len(ce_roms):
	raise Exception("Odd/even CROM mismatch")

# -------------------------------------------------------------------
# From the NEO-SD docs:
# struct NeoFile
# {
#   uint8_t header1, header2, header3, version; // NEO\x01
#   uint32_t PSize, SSize, MSize, V1Size, V2Size, CSize;
#   uint32_t Year;
#   uint32_t Genre;
#   uint32_t Screenshot;
#   uint32_t NGH;
#   uint8_t Name[33];
#   uint8_t Manu[17];
#   // ( filler bytes stripped -- class is filled to size 4096 )
# }

header = [0] * 4096 # Full size of header (4096 bytes)
header[ 0: 4] = b'NEO\x01' # Identification
header[ 4: 8] = combined_len(p_roms).to_bytes(4, byteorder="little")
header[ 8:12] = combined_len(s_roms).to_bytes(4, byteorder="little")
header[12:16] = combined_len(m_roms).to_bytes(4, byteorder="little")
header[16:20] = combined_len(v_roms).to_bytes(4, byteorder="little")
# Ignore V2 roms for now
header[24:28] = (combined_len(co_roms) << 1).to_bytes(4, byteorder="little")
header[28:32] = (int(arguments.year)).to_bytes(4, byteorder="little") # Year
header[32:36] = (genres[arguments.genre]).to_bytes(4, byteorder="little") # Game genre
# Ignore screenshot for now
header[40:44] = (int(arguments.ngh, 0)).to_bytes(4, byteorder="little") # Game NGH number (in BCD)
header[44:44+len(arguments.name)] = arguments.name.encode("ascii") # Game title
header[77:77+len(arguments.company)] = arguments.company.encode("ascii") # Company/Manufacturer
# -------------------------------------------------------------------

if not arguments.silent:
	print("output: %s" % arguments.output)

f = open(arguments.output, 'wb')
f.write(bytes(header))
for data in p_roms: f.write(data)
for data in s_roms: f.write(data)
for data in m_roms: f.write(data)
for data in v_roms: f.write(data)
# Skip v2 (separated) vroms

for (data_odd, data_even) in zip(co_roms, ce_roms):
	f.write(interleave(data_odd, data_even))

f.close()
