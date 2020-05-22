import os
import re

# these should be parameters
SHOW_NAME = "Black Mirror" # no space at the end
SUB_LANGUAGE = "swe"
DIR = '.'

def episode_from_filename(filename): # https://stackoverflow.com/a/9129611
	episode = re.findall(r"(?:s|season)(\d{2}).*?(?:e|x|episode|\n)(\d{2})", filename, re.I)
	return "S" + episode[0][0] + "E" + episode[0][1]

def episode_rename(directory, mode):
	folder = directory # get maybe fullpath here?
	for filename in os.listdir(folder):
		if os.path.isdir(filename) or filename.endswith('.py'):
			continue
		ep = episode_from_filename(filename)
		ext = os.path.splitext(filename)[1]
		if filename.endswith('srt'):
			new_name = SHOW_NAME + "_" + ep + '.' + SUB_LANGUAGE + ext
		else:
			new_name = SHOW_NAME + "_" + ep + ext
		print (filename, "-->", new_name)
		if mode:
			# rename here
			os.rename(filename, new_name)

episode_rename(DIR, False)

yn = input("Proceed with renaming? y/N ").lower()
if yn != "y":
	print ("exiting...")
	sys.exit(1)

episode_rename(DIR, True)