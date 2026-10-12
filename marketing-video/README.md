# Vidéo marketing n8n Hub (9:16)

Vidéo verticale 1080x1920, 30 s, 30 fps : `n8n-hub-marketing-9x16.mp4`.

Régénérer :

```bash
npm install
node render.mjs          # frames/ via Chrome headless (index.html, fonction render(t))
python3 music.py         # music.wav
ffmpeg -framerate 30 -i frames/f_%05d.jpg -i music.wav -c:v libx264 -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -shortest -movflags +faststart n8n-hub-marketing-9x16.mp4
```
