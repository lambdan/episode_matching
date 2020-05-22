I wrote this to automatically rename some of my TV Show boxsets to proper SXXEYY format, using already properely labeled SRT files I found online. 

My workflow:

1. Rip the episodes using [MakeMKV](http://makemkv.com/) or similar software (make sure to get the English subtitles). Get all the MKV files into one folder.
2. Extract the bitmap subtitles from the resulting MKV files using [mkvextract](https://mkvtoolnix.download/doc/mkvextract.html) or similar software, here's an example how to extract all the files on Windows (change the track number, 3, if necessary):
	for %f in (*.mkv) do call mkvextract tracks "%f" 3:"%~nf.sup"
3. OCR the subtitles using [Subtitle Edit](https://www.nikse.dk/subtitleedit/) (Tools -> Batch Convert..., and drop all the .sup's in there). This will take a long time.
4. Put these "unlabeled" SRT files into a folder, such as "unlabeled"
5. Find "labeled" SRT files somewhere else, such as [Subscene](https://subscene.com/) or [Opensubtitles](http://opensubtitles.org/), put all of these into a folder, such as "labeled"
6. Modify the Settings in `match-subtitles.py` to your liking. You probably want a different "prepend" atleast.
7. Run `match-subtitles.py` 
8. Run the resulting rename script in the folder with all the "unlabeled" MKV files from MakeMKV