@echo off

md Frames
for %%f in (*.m*) do (
	ffmpeg -ss 00:03:00 -n -i "%%f" -vf scale=66:50,fps=1,hue=s=0 -t 100 "Frames/%%~nf_-_-_%%d.bmp"
)
pause