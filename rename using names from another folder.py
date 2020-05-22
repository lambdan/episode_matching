import os, re

folder_with_good_names = 'Y:/TV Shows/That 70s Show (1998)'
folder_With_bad_names = './'

def episode_from_filename(filename): # https://stackoverflow.com/a/9129611
	episode = re.findall(r"(?:s|season)(\d{2})(?:e|x|episode|\n)(\d{2})", filename, re.I)
	return "S" + episode[0][0] + "E" + episode[0][1]

print("Reading good names into list")
good_names = []
for f in os.listdir(folder_with_good_names):
	try:
		ep = episode_from_filename(f)
		good_names.append(f)
	except:
		print("Not an episode?", f)

used_episodes = []
old_names = []
new_names = []
print("Matching bad names")
for f in os.listdir(folder_With_bad_names):
	try:
		for name in good_names:
			if episode_from_filename(name) == episode_from_filename(f):
				if episode_from_filename(name) in used_episodes:
					print("Episode already used... this is bad")
					sys.exit(1)
				else:
					new_name = name
					used_episodes.append(episode_from_filename(name))

					break
		final_name = os.path.splitext(new_name)[0] + os.path.splitext(f)[1] # new name + original ext
		print(f, "--->", final_name)
		old_names.append(f)
		new_names.append(final_name)
	except:
		print("Not an episode?", f)
		continue

# verify old_names and new_names is same length
if len(old_names) != len(new_names):
	print("Hmm, not as many names in old_names as in new_names... cant continue")
	sys.exit(1)

yn = input("Proceed with renaming? y/n")
if yn.lower() == 'y':
	# rename
	i = 0
	while i < len(old_names):
		old = old_names[i]
		new = new_names[i]
		os.rename(old,new)
		print(old,"renamed to",new)
		i += 1
else:
	print("OK, canceled")
	sys.exit(1)
