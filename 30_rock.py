#### Settings ####
unlabeled_folder = 'Y:/TV Shows/30 Rock/' # folder with unlabeled videos (disc1_title00.mkv, disc1_title01.mkv)
labeled_folder = 'Y:/TV Shows/30 Rock/new/' # folder with labeled videos (s01e01.mp4, s01e02.mp4)
start_second = 0 # start later if theres a intro right at the start (default: 30)
compare_seconds = 1 # higher value = slower but more confident results. higher values might be a problem if the framerates differ (default: 10)
increment = (1/23.976)
match_avg = 40 # if avg is lower than this: move on (default: 75)
skip_already_matched_episodes = True # True will be much faster as we'll skip checking episodes we already got, but could be much unsafer also if there was a wrong match (default: True)
### End of Settings ###

print ("*** Settings ***")
print ("Unlabeled files folder:", unlabeled_folder)
print ("Labeled files folder:", labeled_folder)
print ("Start second:", start_second)
print ("Compare seconds:", compare_seconds)
print()

video_extensions = ('.mkv', '.mp4', '.avi', '.m4v')
ffmpeg_options = '-loglevel error -vf hue=s=0,scale=100:100'

import re, math, operator, os, sys, random, subprocess, time, tempfile
from PIL import ImageChops, Image
from tqdm import tqdm
import numpy as np
import cv2

if os.path.isfile('rename.bat'):
	os.remove('rename.bat')
if os.path.isfile('Undo_rename.bat'):
	os.remove('Undo_rename.bat')

folder_for_comparisons = './episode_matches/'
if not os.path.isdir(folder_for_comparisons):
	os.makedirs(folder_for_comparisons)


def episode_from_filename(filename): # https://stackoverflow.com/a/9129611
	episode = re.findall(r"(?:s|season)(\d{2})(?:e|x|episode|\n)(\d{2})", filename, re.I)
	return "S" + episode[0][0] + "E" + episode[0][1]

def rmsdiff(im1, im2): # https://stackoverflow.com/a/40176818
	# 0.0 means identical image, so values closer to 0 are probably matches
    # "Calculate the root-mean-square difference between two images"
    diff = ImageChops.difference(im1, im2)
    h = diff.histogram()
    sq = (value*((idx%256)**2) for idx, value in enumerate(h))
    sum_of_squares = sum(sq)
    rms = math.sqrt(sum_of_squares/float(im1.size[0] * im1.size[1]))
    return rms

def FrameIsBlack(img_path): # im is path
	im = cv2.imread(img_path)
	gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
	if np.average(gray) < 20:
		return True
	else:
		return False

def getLength(video):
    result = subprocess.check_output('ffprobe -i "' + video + '" -show_entries format=duration -v quiet -of csv="p=0"', shell=True)
    return result.strip().decode()

def add_comparison_image(im1, im2, im3, y):
	comparison_image = im3
	if comparison_image is None:
		comparison_image = Image.new("RGB", ((im1.size[0]*2)+1, im1.size[1]*compare_seconds))
	w1, h1 = im1.size
	w2, h2 = im2.size
	if h2 > h1:
		height = h2
	elif h1 > h2:
		height = h1
	else:
		height = h1
	y_offset = y * height
	comparison_image.paste(im1,(0,y_offset))
	comparison_image.paste(im2,((w1+1),y_offset))
	#comparison_image.show()
	return comparison_image

lowest = 999
matched_episodes = []

for ula in os.listdir(unlabeled_folder):
	comparison_image = None
	if not ula.lower().endswith(video_extensions):
		#print "skipping " + ula + " - not a video"
		continue
	ulaPath = os.path.abspath(os.path.join(unlabeled_folder , ula))

	#print ("?", ulaPath)

	for la in os.listdir(labeled_folder):

		if not la.lower().endswith(video_extensions):
			continue

		if episode_from_filename(la) in matched_episodes and skip_already_matched_episodes is True:
			continue

		laPath = os.path.abspath(os.path.join(labeled_folder , la))
		ep = episode_from_filename(la) # get sxxeyy from labeled episode

		#pbar = tqdm(total=compare_seconds) # start progress bar
		#pbar.set_description("Comparing [" + ula + "] to [" + la + ']')
		#print ("Comparing [", ula, "] to [", la, ']')

		# compare length, if theyre very different its very unlikely to be a match and thus we skip it
		ulaLength = float( getLength(ulaPath) )
		laLength = float( getLength(laPath) )
		if (ulaLength/laLength) < 0.96 or (ulaLength/laLength) > 1.04: # 0.96 and 1.04 to compensate for PAL 4% speedup
			#pbar.close()
			print("Length differs too much, skipping...", ulaLength, laLength)
			continue

		diffs = [] # values of the diffs are stored here, we later avg it
		sec = start_second 
		iteration = 0
		while iteration < compare_seconds:
			# set up temp files 
			temp1_file_handle, temp1_filename = tempfile.mkstemp('.jpg')
			temp2_file_handle, temp2_filename = tempfile.mkstemp('.jpg')
			ulaImg = temp1_filename
			laImg = temp2_filename

			# use ffmpeg to screenshot videos to the temp files
			# find first not black ula frame
			sec = 0
			print('Finding first not black frame of',ulaPath)
			subprocess.check_output('ffmpeg -y -ss ' + str(sec) + ' -i "' + ulaPath + '" -vframes 1 ' + ffmpeg_options + ' ' + ulaImg, shell=True)
			while FrameIsBlack(ulaImg):
				subprocess.check_output('ffmpeg -y -ss ' + str(sec) + ' -i "' + ulaPath + '" -vframes 1 ' + ffmpeg_options + ' ' + ulaImg, shell=True)
				sec += increment
			print('Found at',sec)
			#cv2.imshow('Unlabeled',cv2.imread(ulaImg))

			sec = 0
			print('Finding first not black frame of',laPath)
			subprocess.check_output('ffmpeg -y -ss ' + str(sec) + ' -i "' + laPath + '" -vframes 1 ' + ffmpeg_options + ' ' + laImg, shell=True)
			while FrameIsBlack(laImg):
				subprocess.check_output('ffmpeg -y -ss ' + str(sec) + ' -i "' + laPath + '" -vframes 1 ' + ffmpeg_options + ' ' + laImg, shell=True)
				sec += increment
			print('Found at',sec)
			#cv2.imshow('Labeled',cv2.imread(laImg))
			
			# open the temp fiels and compare them
			im1 = Image.open(ulaImg)
			im2 = Image.open(laImg)
			diff = rmsdiff(im1,im2) # diff between the two screenshots
			print("diff(lower is better):",diff)
			comparison_image = add_comparison_image(im1, im2, comparison_image, iteration)
			diffs.append(diff)
			avg = sum(diffs)/len(diffs)
			#pbar.set_description("Comparing [" + ula + "] / [" + la + ']: ' + str(round(diff, 2)) + ' (' + str(round(avg, 2)) + ')')

			# clean up tempfiles
			os.close(temp1_file_handle)
			os.remove(temp1_filename)
			os.close(temp2_file_handle)
			os.remove(temp2_filename)

			# update progress bar and iterate
			#pbar.update(1)
			iteration += 1

		#pbar.close()

		if avg < match_avg:
			print("*** Matched! [" + ula + "] seems to be [" + la + "]")
			matched_episode = episode_from_filename(la)
			print("")
			break
		elif avg < lowest:
			lowest = avg
			matched_episode = episode_from_filename(la)

	if matched_episode in matched_episodes:
		print ("Yikes !!! Episode already matched. Cannot continue with confidence. Exiting...")
		sys.exit(1)
	else:
		comparison_image.save(folder_for_comparisons + matched_episode + "-comparison.jpg")
		matched_episodes.append(matched_episode)
		filename = os.path.splitext(la)[0]
		extension = os.path.splitext(ula)[1]
		# write rename scripts
		with open('rename.bat', "a") as fi:
			fi.write('move "' + ula + '" "' + filename + extension + "\"\n")
		with open('Undo_rename.bat', "a") as fi: # same as regular rename but reverse
			fi.write('move "' + filename + extension + '" "' + ula + "\"\n")
