import re, math, operator, os, sys, random, subprocess, time, tempfile
from PIL import ImageChops, Image
from tqdm import tqdm
import numpy as np
import cv2

#### Settings ####
unlabeled_folder = './' # folder with unlabeled videos (disc1_title00.mkv, disc1_title01.mkv)
labeled_folder = 'Y:/TV Shows/That 70s Show (1998)' # folder with labeled videos (s01e01.mp4, s01e02.mp4)
start_second = 0 # start later if theres a intro right at the start (default: 30)
compare_seconds = 1 # higher value = slower but more confident results. higher values might be a problem if the framerates differ (default: 10)
increment = ( 1/23.976 )
skip_already_matched_episodes = True # True will be much faster as we'll skip checking episodes we already got, but could be much unsafer also if there was a wrong match (default: True)
instamatch = 12

debug = False # print black values, seconds, show comparison etc. gets very messy

black_save_file = "first_frames_labeled.txt"
black_save_file2 = "first_frames_unlabeled.txt"

### End of Settings ###
print ("Unlabeled files folder:", os.path.abspath(unlabeled_folder))
print ("Labeled files folder:", os.path.abspath(labeled_folder))
print ("Start second:", start_second)
print ("Instamatch <=", instamatch)
#print ("Compare seconds:", compare_seconds)
print()

video_extensions = ('.mkv', '.mp4', '.avi', '.m4v')
ffmpeg_options = '-loglevel error -vf scale=100:100' # -vf hue=s=0


if os.path.isfile('rename.bat'):
	print("removing old rename file")
	os.remove('rename.bat')
if os.path.isfile('Undo_rename.bat'):
	os.remove('Undo_rename.bat')

folder_for_comparisons = './episode_matches/'
if not os.path.isdir(folder_for_comparisons):
	os.makedirs(folder_for_comparisons)

cache_episode_names = []
cache_episode_first_black = []
cache_unlabeled_names = []
cache_unlabeled_first_black = []

def episode_from_filename(filename): # https://stackoverflow.com/a/9129611
	episode = re.findall(r"(?:s|season)(\d{2})(?:e|x|episode|\n)(\d{2})", filename, re.I)
	return "S" + episode[0][0] + "E" + episode[0][1]

def rmsdiff(im1, im2): # https://stackoverflow.com/a/40176818
	# 0.0 means identical image, so values closer to 0 are probably matches
    # "Calculate the root-mean-square difference between two images"
    diff = ImageChops.difference(im1.convert('LA'), im2.convert('LA')) # .converT(LA) to b&w
    h = diff.histogram()
    sq = (value*((idx%256)**2) for idx, value in enumerate(h))
    sum_of_squares = sum(sq)
    rms = math.sqrt(sum_of_squares/float(im1.size[0] * im1.size[1]))
    return rms

def FrameIsBlack(img_path):
	im = Image.open(img_path)
	colors = im.convert('RGB').getcolors(maxcolors=999999)
	#print("colors:",len(colors))
	if len(colors) < 3000:
		return True
	else:
		return False

def getLength(video):
    result = subprocess.check_output('ffprobe -i "' + video + '" -show_entries format=duration -v quiet -of csv="p=0"', shell=True)
    return result.strip().decode()

lowest = 999
matched_episodes = []

# save/load file with first significant frame
if os.path.isfile(black_save_file):
	print("Load from save file labeled episodes")
	with open(black_save_file) as f:
		lines = f.readlines()
	for l in lines:
		cache_episode_names.append(l.split("|")[0].rstrip())
		cache_episode_first_black.append(float(l.split("|")[1].rstrip()))
else:
	print("Finding first meaningful frame of each labeled episode...")
	for la in os.listdir(labeled_folder):
		if not la.lower().endswith(video_extensions):
			continue
		laPath = os.path.abspath(os.path.join(labeled_folder , la))
		temp2_file_handle, temp2_filename = tempfile.mkstemp('.jpg')
		laImg = temp2_filename
		if laPath in cache_episode_names: # check if in cache
			sec = cache_episode_first_black[cache_episode_names.index(laPath)]
			subprocess.check_output('ffmpeg -y -ss ' + str(sec) + ' -i "' + laPath + '" -vframes 1 ' + ffmpeg_options + ' ' + laImg, shell=True)
		else:
			sec = start_second
			subprocess.check_output('ffmpeg -y -ss ' + str(sec) + ' -i "' + laPath + '" -vframes 1 ' + ffmpeg_options + ' ' + laImg, shell=True)
			while FrameIsBlack(laImg):
				subprocess.check_output('ffmpeg -y -ss ' + str(sec) + ' -i "' + laPath + '" -vframes 1 ' + ffmpeg_options + ' ' + laImg, shell=True)
				sec += increment
			print(os.path.basename(laPath), "at", sec) # found
			cache_episode_names.append(laPath) # add to cache
			cache_episode_first_black.append(float(sec))
	print("Saving for future use...")
	f = open(black_save_file,'w')
	for ep in cache_episode_names:
		s = cache_episode_first_black[cache_episode_names.index(ep)]
		f.write(ep + "|" + str(s))
		f.write("\n")
	f.close()

# extract frames from labeled episodes if that hasnt already been done
labeled_thumbs = []
for ep in cache_episode_names:
	s = cache_episode_first_black[cache_episode_names.index(ep)]
	filename = episode_from_filename(ep) + "_labeled_" + str(s) + ".jpg"
	labeled_thumbs.append(filename)
	if not os.path.isfile(filename):
		print("Extracting", s, "from", ep, "to", filename)
		laPath = ep
		subprocess.check_output('ffmpeg -y -ss ' + str(s) + ' -i "' + laPath + '" -vframes 1 ' + ffmpeg_options + ' ' + filename, shell=True)

# detect troublesome episodes by looking for similar frames
print("Checking for trouble episodes (similar first frames)...")
trouble_episodes = []
lowest = 999
for a in labeled_thumbs:
	im1 = Image.open(a)
	for b in labeled_thumbs:
		if episode_from_filename(a) == episode_from_filename(b): # skip checking against itself
			continue
		im2 = Image.open(b)
		diff = rmsdiff(im1,im2)
		#if diff < lowest:
		#	print("new low",diff,a,b)
		#	lowest = diff
		if diff < 30:
			#print("trouble?", a, b, diff)
			if episode_from_filename(a) not in trouble_episodes:
				trouble_episodes.append(episode_from_filename(a))
			if episode_from_filename(b) not in trouble_episodes:
				trouble_episodes.append(episode_from_filename(b))
print("These episodes have very similar first frames, you'll have to manually rename them:", trouble_episodes)

################

# save/load/find first signifcant frame in unlabeled videos
if os.path.isfile(black_save_file2):
	print("Load from save file unlabeled frames")
	with open(black_save_file2) as f:
		lines = f.readlines()
	for l in lines:
		cache_unlabeled_names.append(l.split("|")[0].rstrip())
		cache_unlabeled_first_black.append(float(l.split("|")[1].rstrip()))
else:
	print("Finding first meaningful frame of each UNlabeled episode...")
	for la in os.listdir(unlabeled_folder):
		if not la.lower().endswith(video_extensions):
			continue
		laPath = os.path.abspath(os.path.join(unlabeled_folder , la))
		temp2_file_handle, temp2_filename = tempfile.mkstemp('.jpg')
		laImg = temp2_filename
		if laPath in cache_unlabeled_names: # check if in cache
			sec = cache_unlabeled_first_black[cache_episode_names.index(laPath)]
			subprocess.check_output('ffmpeg -y -ss ' + str(sec) + ' -i "' + laPath + '" -vframes 1 ' + ffmpeg_options + ' ' + laImg, shell=True)
		else:
			sec = start_second
			subprocess.check_output('ffmpeg -y -ss ' + str(sec) + ' -i "' + laPath + '" -vframes 1 ' + ffmpeg_options + ' ' + laImg, shell=True)
			while FrameIsBlack(laImg):
				subprocess.check_output('ffmpeg -y -ss ' + str(sec) + ' -i "' + laPath + '" -vframes 1 ' + ffmpeg_options + ' ' + laImg, shell=True)
				sec += increment
			print(os.path.basename(laPath), "at", sec) # found
			cache_unlabeled_names.append(laPath) # add to cache
			cache_unlabeled_first_black.append(float(sec))
	print("Saving for future use...")
	f = open(black_save_file2,'w')
	for ep in cache_unlabeled_names:
		s = cache_unlabeled_first_black[cache_unlabeled_names.index(ep)]
		f.write(ep + "|" + str(s))
		f.write("\n")
	f.close()

# extract frames from UNlabeled episodes if that hasnt already been done
unlabeled_thumbs = []
for ep in cache_unlabeled_names:
	s = cache_unlabeled_first_black[cache_unlabeled_names.index(ep)]
	filename = ep + "_" + str(s) + ".jpg"
	unlabeled_thumbs.append(filename)
	if not os.path.isfile(filename):
		print("Extracting", s, "from", ep, "to", filename)
		laPath = ep
		subprocess.check_output('ffmpeg -y -ss ' + str(s) + ' -i "' + laPath + '" -vframes 1 ' + ffmpeg_options + ' "' + filename + '"', shell=True)

#####################

trouble_matches = []
# now compare unlabeled with labeled images
for ula in unlabeled_thumbs:
	u = Image.open(ula)

	# get original filename from thumb name
	for i in os.listdir(unlabeled_folder):
		if os.path.basename(ula).startswith(i):
			original_name = i
			#print(ula,"comes from",i)
			#sys.exit(1)
			break

	lowest = 999
	for la in labeled_thumbs: # iterate labeled images
		print("Trying '" + original_name + "' with", episode_from_filename(la), end="\t")
		l = Image.open(la)
		# compare images
		diff = rmsdiff(u,l)

		comparison_image = Image.new("RGB", (200,100))
		comparison_image.paste(u,(0,0))
		comparison_image.paste(l,((100),0))

		if diff < lowest:
			lowest = diff
			matched_episode = episode_from_filename(la)
			best_comparison_image = comparison_image
			best_ula = original_name
			best_la = episode_from_filename(la)
			if diff < instamatch:
				print("<--- Instamatched! (tm)")
				break
			else:
				print("<--- best match so far!", diff)
		else:
			#print("(best match so far: " + matched_episode + ", " + str(lowest) + ")")
			print()

	if matched_episode in matched_episodes:
		print ("Error! Episode already matched. Cannot continue with confidence. Exiting...")
		sys.exit(1)
	else:
		if matched_episode in trouble_episodes:
			print('"' + best_ula + "' seems to be a trouble episode\n")
			best_comparison_image.save(folder_for_comparisons + "!TROUBLE_" + matched_episode + "-" + str(lowest) + "-ULA_" + os.path.basename(best_ula) + "-LA_" + os.path.basename(best_la) + "-comparison.jpg")
			trouble_matches.append(best_ula)
			continue
		else:
			print('"' + best_ula + "' seems to be", matched_episode,"\n")
			best_comparison_image.save(folder_for_comparisons + matched_episode + "-" + str(lowest) + "-ULA_" + os.path.basename(best_ula) + "-LA_" + os.path.basename(best_la) + "-comparison.jpg")
			matched_episodes.append(matched_episode)
			#lowest = 9999999999
			filename = os.path.splitext(best_la)[0]
			extension = os.path.splitext(original_name)[1]
			# write rename scripts
			with open('rename.bat', "a") as fi:
				fi.write('move "' + best_ula + '" "' + filename + extension + "\"\n")
			with open('Undo_rename.bat', "a") as fi: # same as regular rename but reverse
				fi.write('move "' + filename + extension + '" "' + ula + "\"\n")

print("Done")
print("Trouble matches:", trouble_matches)
print("Trouble episodes:", trouble_episodes)
print("You'll have to manually match those ^^")