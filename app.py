from flask import Flask, render_template, request
from midiutil import MIDIFile
from pydub import AudioSegment
from music21 import stream, note, metadata, environment
import os
import glob

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 정간보 음 → MIDI 음 매핑
note_mapping = {
    '黃': 60, '太': 62, '仲': 64, '林': 65,
    '南': 67, '應': 69, '潢': 71, '溝': 72,
}

def jeongganbo_to_midi_and_score(text, midi_path, image_prefix):
    midi = MIDIFile(1)
    track, time = 0, 0
    midi.addTrackName(track, time, "Jeongganbo")
    midi.addTempo(track, time, 120)

    s = stream.Score()
    p = stream.Part()
    p.id = "Piano"
    p.append(metadata.Metadata(title="Converted from Jeongganbo"))

    duration = 1
    volume = 100
    channel = 0
    note_found = False

    for char in text:
        if char in note_mapping:
            pitch = note_mapping[char]
            midi.addNote(track, channel, pitch, time, duration, volume)
            n = note.Note(pitch)
            n.quarterLength = 1
            p.append(n)
            time += duration
            note_found = True

    if not note_found:
        return False, None

    s.append(p)

    # MIDI 저장
    with open(midi_path, 'wb') as f:
        midi.writeFile(f)

    # Musescore 경로 지정 (macOS 기준)
    env = environment.UserSettings()
    env["musescoreDirectPNGPath"] = "/Applications/MuseScore 4.app/Contents/MacOS/mscore"

    # 서양 악보 이미지 생성
    s.write("musicxml.png", fp=image_prefix)
    generated_images = sorted(
        glob.glob(f"{image_prefix}*.png"), key=os.path.getmtime, reverse=True
    )
    return True, os.path.basename(generated_images[0]) if generated_images else None

def midi_to_mp3(midi_path, mp3_path):
    wav_path = midi_path.replace(".mid", ".wav")
    os.system(f"timidity {midi_path} -Ow -o {wav_path}")
    sound = AudioSegment.from_wav(wav_path)
    sound.export(mp3_path, format="mp3")
    os.remove(wav_path)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith(".txt"):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()

            midi_path = os.path.join(OUTPUT_FOLDER, "jeongganbo.mid")
            mp3_path = os.path.join(OUTPUT_FOLDER, "jeongganbo.mp3")
            image_prefix = os.path.join(OUTPUT_FOLDER, "score")

            success, image_file = jeongganbo_to_midi_and_score(text, midi_path, image_prefix)
            if success:
                midi_to_mp3(midi_path, mp3_path)
                return render_template(
                    "index.html",
                    mp3_generated=True,
                    image_path=f"output/{image_file}",
                    jeongganbo_text=text
                )
            else:
                return render_template("index.html", error="⚠ No valid Jeongganbo notes found.")
        else:
            return render_template("index.html", error="Please upload a .txt file.")
    return render_template("index.html")

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
