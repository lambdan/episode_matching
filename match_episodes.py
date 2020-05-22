#### Settings ####
unlabeled_folder = 'I:/MakeMKV/That70sShow-Bluray' # folder with unlabeled videos (disc1_title00.mkv, disc1_title01.mkv)
labeled_folder = 'T:/TV Shows - Svensk text/That 70s Show (1998)/Blu-Ray 8Mbps' # folder with labeled videos (s01e01.mp4, s01e02.mp4)
giveUpAfter = 3 # if the avg is >100 after this many comparisons, give up and go to the next video. this affects speed the most
sampleSize = 5 # how many screenshots to compare
videoDuration = 300 # how many seconds of video to take random screenshots from. lower if framerates differ
instaMatch = 25 # move on to next episode if avg is lower than this, instead of going through all videos
safe = False # skip trying to match with episodes that have already been matched. will speed up, especially the further it goes, but might be unsafe if it was an inaccurate match or if there are duplicates
### End of Settings ###

video_extensions = ('.mkv', '.mp4', '.avi', '.m4v')
ffmpeg_options = '-loglevel error -vf scale=640:360'

import re, math, operator, os, sys, random, subprocess, time
from PIL import ImageChops, Image

if os.path.isfile('rename.bat'):
	os.remove('rename.bat')
if os.path.isfile('Undo_rename.bat'):
	os.remove('Undo_rename.bat')

def episode_from_filename(filename): # https://stackoverflow.com/a/9129611
	episode = re.findall(r"(?:s|season)(\d{2})(?:e|x|episode|\n)(\d{2})", filename, re.I)
	return "S" + episode[0][0] + "E" + episode[0][1]

def rmsdiff(im1, im2): # https://stackoverflow.com/a/40176818
	# 0.0 means identical image, so values closer to 0 are probably matches
    "Calculate the root-mean-square difference between two images"
    diff = ImageChops.difference(im1, im2)
    h = diff.histogram()
    sq = (value*((idx%256)**2) for idx, value in enumerate(h))
    sum_of_squares = sum(sq)
    rms = math.sqrt(sum_of_squares/float(im1.size[0] * im1.size[1]))
    return rms

matchedEps = [] # used for dupe checking

for ula in os.listdir(unlabeled_folder):
	if not ula.lower().endswith(video_extensions):
		#print "skipping " + ula + " - not a video"
		continue
	ulaPath = os.path.abspath(os.path.join(unlabeled_folder , ula))
	bestMatchEp = ""
	bestMatchVal = 999
	print ula + ":"
	for la in os.listdir(labeled_folder):
		if not la.lower().endswith(video_extensions):
			#print "skipping " + la + " - not a video"
			continue
		ep = episode_from_filename(la)
		if not safe and ep in matchedEps:
			continue
		laPath = os.path.abspath(os.path.join(labeled_folder , la))

		i = 1
		values = []
		print "\t" + ep,
		while i <= sampleSize:
			timeStamp = random.randint(1,videoDuration) # we take screenshot at random timestamp

			# unlabeled screenshot
			ulaImg = ep + "." + str(timeStamp) + '.unlabeled' + str(time.time()) + '.jpg'
			subprocess.check_output('ffmpeg -y -ss ' + str(timeStamp) + ' -i "' + ulaPath + '" -vframes 1 ' + ffmpeg_options + ' ' + ulaImg, shell=True)
			# labeled screenshot
			laImg = ep + "." + str(timeStamp) + '.labeled' + str(time.time()) + '.jpg'
			subprocess.check_output('ffmpeg -y -ss ' + str(timeStamp) + ' -i "' + laPath + '" -vframes 1 ' + ffmpeg_options + ' ' + laImg, shell=True)
			im1 = Image.open(ulaImg)
			im2 = Image.open(laImg)
			diff = rmsdiff(im1,im2) # diff between the two screenshots

			# remove temp images # FIXME: use python temp files instead?
			try: # i sometimes get WindowsError file in use without this
				os.remove(ulaImg)
				os.remove(laImg)
			except:
				print "WARNING: couldn't delete temp images, you have to delete them manually later"

			#print str(diff), # very verbose
			values.append(diff)
			i += 1
			if len(values) >= giveUpAfter and (sum(values)/len(values) > 100): # if the avg is > 100 after n samples: give up
				break
		avg = sum(values)/len(values)

		print "= " + str(avg) + "\t" + str(len(values)) +" samples",
		if avg <= bestMatchVal and avg < 100:
			bestMatchVal = avg
			bestMatchEp = ep
			print "\tmatch?"
		if avg <= instaMatch:
			break
		print ""

	if bestMatchVal == 999:
		print "WARNING: could not match video " + ula
	else:
		print "" + ula + " --> " + bestMatchEp + " (" + str(bestMatchVal) + ")\n"

	if bestMatchEp in matchedEps:
		print "ERROR: episode already matched, cannot continue with confidence. exiting..."
		sys.exit(1)
	else:
		matchedEps.append(bestMatchEp)
		extension = os.path.splitext(ula)[1]
		# write rename scripts
		with open('rename.bat', "a") as fi:
			fi.write('move "' + ula + '" "' + bestMatchEp + extension + "\"\n")
		with open('Undo_rename.bat', "a") as fi: # same as regular rename but reverse
			fi.write('move "' + bestMatchEp + extension + '" "' + ula + "\"\n")
