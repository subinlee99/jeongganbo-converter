# Jeongganbo to Western Music Converter 🎼

A web app that converts traditional Korean Jeongganbo music notation into Western-style sheet music and playable audio.

## 🎥 Demo Video

👉 [Click here to watch the demo](https://drive.google.com/file/d/19a9ZdDMI1TJtYmuJwA4hTnAPQUrK9U-f/view?usp=sharing)

### 📊 Diagram

<pre> ## 📊 Diagram – How It Works ``` [Jeongganbo .txt Input] ↓ [Parser: Map to MIDI Notes] ↓ ┌─────┴─────┐ ↓ ↓ [MIDI → MP3] [Sheet Music Image] (timidity + (music21 + pydub) matplotlib) ↓ ↓ [Web App Interface – Flask] ├── Audio Playback ├── Sheet Music Preview └── Original + Converted Text Side-by-Side ``` </pre>

## ✅ Features

- Upload Jeongganbo **text files (.txt)**
- Automatically convert to:
  - 🎼 Western sheet music (image preview)
  - 🎵 MIDI → MP3 audio (auto playback in browser)
- View original Jeongganbo text and converted result side-by-side

## 💡 How It Works

1. Parses Jeongganbo text and maps to MIDI notes
2. Converts MIDI → MP3 using `timidity` + `pydub`
3. Generates visual sheet music using `music21` and `matplotlib`
4. Renders results on a simple web interface (Flask)

## 🧪 Optional Upgrades

- **Option 1:** Upload Jeongganbo **images** and use OCR to auto-parse notation
- **Option 2:** Playback with **Korean traditional instrument samples** instead of piano

## ⚠ Known Issues

- Current note matching is **incomplete** — playback may sound unnatural
- Mapping algorithm needs refinement (interviewees also noted limitations in aligning Jeongganbo with Western notation)

## 🛠 Requirements

Install dependencies:

```bash
pip install -r requirements.txt
brew install timidity  # for MIDI to audio conversion (macOS)
