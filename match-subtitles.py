from difflib import SequenceMatcher
import os, re, sys

######### Settings #########
prepend = "The Sopranos " # will be prepended to every renamed file
unlabeled = "./unlabeled/" # where your unlabeled SRT files are
labeled = "./labeled/" # where the labeled SRT files are
video_ext = '.mkv' # video extension
match_needed = 0.2 # required ratio for a instant match (i've had matches as low as 0.05 so 0.2 should be super safe)
make_rename_sh = False # make rename.sh (linux/macos)
make_rename_bat = True # make rename.bat (windows)
############################

def episode_from_filename(filename): # https://stackoverflow.com/a/9129611
	episode = re.findall(r"(?:s|season)(\d{2})(?:e|x|episode|\n)(\d{2})", filename, re.I)
	return "S" + episode[0][0] + "E" + episode[0][1]

def renameScript(original, renamed):
	if make_rename_sh:
		with open('rename.sh', 'a') as fi:
			fi.write('mv "' + original + '" "' + renamed + "\"\n")
	if make_rename_bat:
		with open('rename.bat', 'a') as fi:
			fi.write('move "' + original + '" "' + renamed + "\"\n")

highest = 0
used_subtitles = []
for uf in os.listdir(unlabeled):
	if uf.lower().endswith('srt'):
		text1 = open(os.path.abspath(unlabeled + uf)).read()
		
		for lf in os.listdir(labeled):
			if lf.lower().endswith('srt') and lf not in used_subtitles:
				print uf + " <-> " + lf + " = ",
				text2 = open(os.path.abspath(labeled + lf)).read()
				m = SequenceMatcher(None, text1, text2) # https://stackoverflow.com/a/1334758
				ratio = m.ratio()
				print ratio
				if ratio > highest:
					highest = ratio
					highest_names = [uf, lf] #highest_names[1] = labeled subtitle
				if ratio >= match_needed:
					break
	old_name = os.path.splitext(uf)[0] + video_ext
	new_name = prepend + episode_from_filename(highest_names[1]) + video_ext
	print old_name + " --> " + new_name + " (" + str(highest) + ")\n"
	highest = 0
	used_subtitles.append(highest_names[1])
	renameScript(old_name, new_name)