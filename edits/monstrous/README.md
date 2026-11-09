# MONSTROUS — hype edit

`monstrous_edit.mp4`: a 14.8 s vertical edit (1080×1920, 60 fps, H.264 + 320 kbps AAC)
built from a 9.5 s phone clip of a can being tapped and cracked open.
The video and audio are generated entirely by the scripts here: no stock music, samples or
templates. The only recorded sounds are the taps and the crack from the original clip.

## Structure (150 BPM, everything lands on the grid)

| time | section | picture | sound |
|---|---|---|---|
| 0.0–1.6 | Intro | fluorescent-flicker reveal, slow push-in, `ZERO SUGAR.` → `ZERO MERCY.` title slams | filtered "underwater" phonk cowbell, dark pad, sub booms, electric zaps |
| 1.6–3.2 | Taps | three taps on the can, one re-cut to land on the beat; zoom punch, shake and flash on each | real tap sounds layered with metal clank + sub thump, filter opens |
| 3.2–4.8 | Groove | speed-ramped velocity edit with motion blur | kick / clap / hats, clean sub |
| 4.8–6.0 | Build | ramps into optical-flow slow-mo, pushes into the tab, colour drains, rumble shake | snare roll, riser, high-pass sweep |
| 6.0–6.4 | Gap | near-freeze on the tab | music cuts out, heartbeat, reverse-reverb crack |
| 6.4–8.0 | **Drop** | crack replayed wide → mid → extreme close, white/green flashes, shockwave, spray particles, anamorphic flare, `MONSTROUS` | crack + boom + crash, distorted 808s with slides |
| 8.0–9.6 | Velocity | beat-locked speed ramps on the opened can | full beat, hat rolls |
| 9.6–11.2 | Flash cuts | 8 cuts on 8th notes recapping the whole clip (B&W / colour / mirror / invert / glitch) | swishes and shutter ticks, crack on the cut |
| 11.2–12.8 | Hero | slow push on the open can, specular light sweep, caption | breakdown with a shimmer hit, drums return with a fill |
| 12.8–14.8 | Outro | freeze, desaturate, fade, `STAY MONSTROUS.` letter reveal | end hit, tape-stop, reverb tail |

## Files

- `timeline.py` — the edit decision list: tempo grid, cuts/retimes, camera moves, drum grid
- `fxcues.py` — the FX cue sheet (punches, shakes, flashes, glitches, particles, text), shared with the audio so every visual hit has a sound
- `prep.py` — decodes the 4K source at its real (variable) frame timestamps and computes optical flow for slow-mo
- `make_audio.py` — synthesizes the phonk BGM and sound design, mixes, compresses and limits (~-9.4 LUFS, -1 dBFS peak)
- `render.py` — renders every frame: optical-flow retiming, virtual camera with motion blur, grade and relight, bloom, flares, particles, shockwave, chromatic aberration, glitch, type, grain
- `build.sh` — runs the whole pipeline

```bash
pip install numpy scipy opencv-python-headless pillow
./build.sh path/to/source.mp4
```
