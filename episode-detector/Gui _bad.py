import re, math, operator, os, sys, easygui, threading, time
from PIL import ImageChops, Image, ImageTk
import Tkinter as tk
from natsort import natsorted

tool_version = '0.1'

# Default settings
accuracy = 20 
required_matches = 20 
start_restart_multiplier = 100
ext = '.mkv' 
separator = '_-_-_' 
make_comparison_images = False

unlabeled_folder = os.path.abspath('input/')
labeled_folder = os.path.abspath('dvds/')

valid_image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
comparison_image = None

if os.name == 'nt': # if windows enable rename.bat
	make_rename_bat = True
	make_rename_sh = False
else:
	make_rename_sh = True
	make_rename_bat = False

running = False


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

def most_common(lst): # https://stackoverflow.com/a/1518632
	return max(set(lst), key=lst.count)

def add_comparison_image(im1, im2):
	global matches
	global comparison_image
	w1, h1 = im1.size
	w2, h2 = im2.size
	if h2 > h1:
		height = h2
	elif h1 > h2:
		height = h1
	else:
		height = h1
	y_offset = (len(matches)-1) * height
	comparison_image.paste(im1,(0,y_offset))
	comparison_image.paste(im2,((w1+1),y_offset))

def liveMatch(im1,im2):
	w1, h1 = im1.size
	w2, h2 = im2.size
	total_width = w1+w2
	total_height = max(h1,h2)
	photo = Image.new('RGB', (total_width, total_height))
	photo.paste(im1,(0,0))
	photo.paste(im2,((w1+1),0))
	updateWindowImages('middle', photo)

def updateWindowImages(which, pic):
	w, h = pic.size
	upscale = pic.resize( (w,h), 1 )
	photo = ImageTk.PhotoImage(upscale)
	if which == 'left':
		img1Panel.config(image=photo)
		img1Panel.photo_ref = photo
	elif which == 'right':
		img2Panel.config(image=photo)
		img2Panel.photo_ref = photo
	elif which == 'middle':
		imgPanel.config(image=photo)
		imgPanel.photo_ref = photo

def setUnlabeledFolder():
	global unlabeled_folder
	unlabeled_folder = os.path.abspath(easygui.diropenbox())
	labelUnlabeledText.set(unlabeled_folder)

def setLabeledFolder():
	global labeled_folder
	labeled_folder = os.path.abspath(easygui.diropenbox())
	labelLabeledText.set(labeled_folder)

def toggle():
	global running
	if running:
		updateStatus('Starting', True)
		running = False
	elif not running:
		updateStatus('Stopping', True)
		updateSecondLabel('Stopping')
		running = True

def updateStatus(msg, shouldPrint):
	if shouldPrint:
		print msg.strip('\n')
	labelStatus.configure(text=msg)

def updateSecondLabel(msg):
	print msg.strip('\n')
	labelSecond.configure(text=msg)

def EpisodeDetector():
	global matches
	global comparison_image
	global valid_image_extensions
	global accuracy
	global required_matches
	global running
	global start_restart_multiplier

	if running:
		print "Unlabeled Folder: " + unlabeled_folder
		print "Labeled Folder: " + labeled_folder
		updateStatus('Starting', True)
		updateSecondLabel('Building file lists...')
		unlabeled_files = natsorted([f for f in os.listdir(unlabeled_folder) if os.path.isfile(os.path.join(unlabeled_folder, f)) if f.endswith(valid_image_extensions)])
		labeled_files = natsorted([f for f in os.listdir(labeled_folder) if os.path.isfile(os.path.join(labeled_folder, f)) if f.endswith(valid_image_extensions)])

		start_files = len(unlabeled_files)

		updateStatus('Running', True)
		updateSecondLabel('No matches')

		comparison_image = None
		u = 0
		l = 0
		restart_multiplier = start_restart_multiplier
		matches = []
		matches_percent = []
		matched_videos = 0

		ulab = []
		lab = []
		while len(unlabeled_files) > 0:
			if not running:
				updateStatus('Stopped', True)
				updateSecondLabel('Stopped')
				break

			#print len(labeled_files)

			if l >= len(labeled_files) or l >= restart_multiplier:
				updateSecondLabel('Restarting (' + str(restart_multiplier) + ')')
				u += 1
				l = 0
				restart_multiplier = restart_multiplier + start_restart_multiplier

			ulab = unlabeled_files[u]
			lab = labeled_files[l]


			im1 = Image.open( os.path.join(unlabeled_folder, ulab))
			videofile = ulab.split(separator,1)[0]

			im2 = Image.open( os.path.join(labeled_folder, lab))
			epname = episode_from_filename(lab)

			# useful for debugging
			#updateWindowImages('left', im1)
			#updateWindowImages('right', im2)

			if comparison_image is None:
				comparison_image = Image.new("RGB", ((im1.size[0]*2)+1, im1.size[1]*required_matches))

			diff = rmsdiff(im1,im2)
			#updateStatus('Trying ' + videofile + '\nwith ' + epname + "\n(%.2f %%)" % diff)
			#updateStatus('' + str(files_left) + '/' + str(start_files) + '\n' + str(matched_videos) + ' matched videos')
			
			liveMatch(im1,im2)

			if diff <= accuracy:
				updateSecondLabel('Matched ' + epname + ' (%.2f)' % diff)
				matches.append(epname)
				matches_percent.append(diff)
				add_comparison_image(im1,im2)
				del unlabeled_files[u]
				del labeled_files[l]
				u += 1
				l=0
				time.sleep(0.25)
				restart_multiplier = start_restart_multiplier
			
			#print matches
			if len(matches)  >= required_matches: # video found
				print videofile + " --> " + most_common(matches)
				matched_videos += 1

				if make_rename_sh is True:
					renameScript(videofile, most_common(matches), 'sh')

				if make_rename_bat is True:
					renameScript(videofile, most_common(matches), 'bat')

				if make_comparison_images is True:
					comparison_image.save(most_common(matches) + "-comparison.jpg")

				# clear out found from the file lists
				unlabeled_files = [x for x in unlabeled_files if not x.startswith(videofile)]
				labeled_files = [x for x in labeled_files if not episode_from_filename(x) == epname]

				# reset values
				u=0
				l=0
				restart_multiplier = start_restart_multiplier
				comparison_image = None
				matches = []
				matches_percent = []
			else:
				l+=1

			files_left = start_files - len(unlabeled_files)
			perc = 100 * float(files_left)/float(start_files)
			updateStatus('%.0f%% complete\n' % perc + str(matched_videos) + ' matched videos', False)
		running = False
		updateSecondLabel("Finished")
	thread = threading.Thread(target=EpisodeDetector)
	thread.daemon = True
	thread.start()

def renameScript(original, renamed, extension):
	# ext is video extension
	if extension == 'sh':
		with open('rename.sh', 'a') as fi:
			fi.write('mv "' + original + ext + '" "' + renamed + ext + "\"\n")
	elif extension == 'bat':
		with open('rename.bat', 'a') as fi:
			fi.write('move "' + original + ext + '" "' + renamed + ext + "\"\n")

def updateSettings():
	global running
	global accuracy
	global ext
	global required_matches
	global separator
	global start_restart_multiplier
	global make_comparison_images
	global make_rename_bat
	global make_rename_sh
	accuracy = int(accuracyE.get())
	ext = str(extensionE.get())
	required_matches = int(requiredMatchesE.get())
	start_restart_multiplier = int(restartMultiplierE.get())
	separator = str(separatorE.get())
	make_comparison_images = bool(comparisonImageBool.get())
	make_rename_bat = bool(renameBatBool.get())
	make_rename_sh = bool(renameShBool.get())
	updateSecondLabel("Updated settings")
	print 'accuracy: ' + str(accuracy)
	print 'req matches: ' + str(required_matches)
	print 'start restart multiplier: ' + str(start_restart_multiplier)
	print 'extension: ' + str(ext)
	print 'separator: ' + str(separator)
	print 'make comparison images: ' + str(make_comparison_images)
	print 'make rename bat: ' + str(make_rename_bat)
	print 'make rename sh: ' + str(make_rename_sh)
	running = False # stop matching if we change settings
	getSettings()

def getSettings():
	global accuracy
	global ext
	global required_matches
	global start_restart_multiplier
	global separator
	global make_comparison_images
	global make_rename_bat
	global make_rename_sh
	accuracyS.set(accuracy)
	extensionS.set(ext)
	requiredMatchesS.set(required_matches)
	restartMultiplierS.set(start_restart_multiplier)
	separatorS.set(separator)
	comparisonImageBool.set(make_comparison_images)
	renameBatBool.set(make_rename_bat)
	renameShBool.set(make_rename_sh)

root = tk.Tk()
root.wm_title("episode-detector")

# Unlabeled folder
labelUnlabeledText = tk.StringVar()
labelUnlabeledText.set(unlabeled_folder)
buttonSetUnlabeled = tk.Button(root, text = 'Unlabeled Folder', command = setUnlabeledFolder)
buttonSetUnlabeled.grid(row=0,column=0,sticky='WE',padx=5,pady=5)
labelUnlabeled = tk.Label(root, textvariable=labelUnlabeledText)
labelUnlabeled.grid(row=0,column=1,sticky='W',padx=5,pady=5,columnspan=3)

# Labeled folder
labelLabeledText = tk.StringVar()
labelLabeledText.set(labeled_folder)
buttonSetLabeled = tk.Button(root, text = 'Labeled Folder', command = setLabeledFolder)
buttonSetLabeled.grid(row=1,column=0,sticky='WE',padx=5,pady=5)
labelLabeled = tk.Label(root, textvariable=labelLabeledText)
labelLabeled.grid(row=1,column=1,sticky='W',padx=5,pady=5,columnspan=3)

# settings
accuracyLabel = tk.Label(root, text='Accuracy')
accuracyLabel.grid(row=4,column=0,sticky='E',padx=5,pady=5)
accuracyS = tk.StringVar()
accuracyE = tk.Entry(root, textvariable=accuracyS)
accuracyE.grid(row=4,column=1,sticky='W',padx=5,pady=5)

requiredMatchesLabel = tk.Label(root, text='Required Matches')
requiredMatchesLabel.grid(row=5,column=0,sticky='E',padx=5,pady=5)
requiredMatchesS = tk.StringVar()
requiredMatchesE = tk.Entry(root, textvariable=requiredMatchesS)
requiredMatchesE.grid(row=5,column=1,sticky='W',padx=5,pady=5)

restartMultiplierLabel = tk.Label(root, text='Restart Multiplier')
restartMultiplierLabel.grid(row=6,column=0,sticky='E',padx=5,pady=5)
restartMultiplierS = tk.StringVar()
restartMultiplierE = tk.Entry(root, textvariable=restartMultiplierS)
restartMultiplierE.grid(row=6,column=1,sticky='W',padx=5,pady=5)

extensionLabel = tk.Label(root, text='Video Extension')
extensionLabel.grid(row=7,column=0,sticky='E',padx=5,pady=5)
extensionS = tk.StringVar()
extensionE = tk.Entry(root, textvariable=extensionS)
extensionE.grid(row=7,column=1,sticky='W',padx=5,pady=5)

separatorLabel = tk.Label(root, text='Screenshot Separator')
separatorLabel.grid(row=8,column=0,sticky='E',padx=5,pady=5)
separatorS = tk.StringVar()
separatorE = tk.Entry(root, textvariable=separatorS)
separatorE.grid(row=8,column=1,sticky='W',padx=5,pady=5)

comparisonImageBool = tk.BooleanVar()
comparisonImageCB = tk.Checkbutton(root, text='Save Comparison Images', variable=comparisonImageBool)
comparisonImageCB.grid(row=4,column=2,padx=5,pady=5,sticky='W')

renameBatBool = tk.BooleanVar()
renameBatCB = tk.Checkbutton(root, text='Make rename.bat', variable=renameBatBool)
renameBatCB.grid(row=5,column=2,padx=5,pady=5,sticky='W')

renameShBool = tk.BooleanVar()
renameShCB = tk.Checkbutton(root, text='Make rename.sh', variable=renameShBool)
renameShCB.grid(row=6,column=2,padx=5,pady=5,sticky='W')


#buttonUpdateSettings = tk.Button(root, text = 'Apply', command = updateSettings)
#buttonUpdateSettings.grid(row=9,column=0,padx=5,pady=5,columnspan=3,sticky="NEWS")
buttonUpdateSettings = tk.Button(root, text = 'Apply', command = updateSettings)
buttonUpdateSettings.grid(row=7,column=2,padx=5,pady=5,columnspan=3,rowspan=2,sticky="NEWS")

buttonStart = tk.Button(root, text = 'Start/Stop', command = toggle)
buttonStart.grid(row=10,column=0,padx=5,pady=5,columnspan=3,sticky="NEWS")

labelStatus = tk.Label(text="Not Running")
labelStatus.grid(row=11,column=0,padx=5,pady=5,columnspan=3,sticky="NEWS")

img1Panel = tk.Label(root)
img1Panel.grid(row=13,column=0)

img2Panel = tk.Label(root)
img2Panel.grid(row=13,column=1)

imgPanel = tk.Label(root)
imgPanel.grid(row=12,column=0,padx=5,pady=5,sticky="NEWS",columnspan=3)

labelSecond = tk.Label(text='episode-detector ' + tool_version)
labelSecond.grid(row=14,column=0,sticky="W",columnspan=3)

root.after(1, getSettings)
root.after(100, EpisodeDetector)
#root.after(100, updateWindowImage)
root.mainloop()