# HERE BE DRAGONS !!!

These are scripts I've written to help myself not have to manually check every video and see what episode it is. 

**THEY ARE VERY MESSY AND I REALLY DONT PLAN FOR ANYONE ELSE TO USE THEM. THE CODE IS MESSY, THE VARIABLE NAMES ARE MESSY, THEY MOVE FILES AROUND A LOT ON YOUR HARD DRIVE**

Even I don't really know or remember how some of them work. I usually spend a lot of time fine tuning them for the specific show I am looking to rename, which usually turns into me completely rewriting them for that specific show.

The general idea is that we find something unique about an episode we know has the right "labeled" name (S01E01 etc.), and then try to find that same thing in the unorganized "unlabeled" (Disc_1_t00 etc.) file.

I have done this through many different ways throughout the years:

- Compare runtimes down to the second or milliseconds
	- Usually doesn't work very well because a lot of episodes will have very similar lengths
- Compare frames
	- Usually works the most reliably but is very finicky and messy
	- You can compare:
		- the first not black frame
			- Works well for shows that start right away with a unique frame (like _30 Rock_)
			- Doesn't work well for shows that start with an intro (like _The Sopranos_)
			- Can work with shows that start very similarily (like _That 70s Show_) but requires fine tuning the black threshold
				- But even then I added a "trouble episode" feature that looks for similar first frames and doesnt attempt to rename those
		- multiple frames in a row or scattered around the video
			- Would give the most reliability but is very slow and messy
- fuzzy matching subtitles
	- Works very well if you have identical subtitles (obviously)
	- Works fairly well if you have similar subtitles
	- Maybe a possibility to compare display times?
	- I've used this for _The Sopranos_ by OCR scanning the blu-ray subtitle and then doing a very fuzzy match
		- Kinda annoying, or very, annoying to do OCR scans (blurays/dvds rarely come with plain texts)
- audio
	- I think this in area I need to investigate more because i think it has great potential and would probably be faster than dealing with video
	- I have one idea to do speech-to-text and compare that
	- Another idea maybe to compare wave forms? 
	- I think I once tried doing lossless audio rips, converting them to WAV, and comparing
		- Worked but unfortunately rips aren't always bit identical so it ultimately didnt

Ultimately all of this is very messy but maybe you find it fun to look into my insanity.