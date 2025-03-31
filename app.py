from flask import Flask, render_template, request
from midiutil import MIDIFile
from pydub import AudioSegment
from music21 import converter, instrument, metadata, environment
import matplotlib
matplotlib.use("Agg")  # for headless environments like Render
import matplotlib.pyplot as plt
import os
import platform

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Jeongganbo note to MIDI pitch mapping
note_mapping = {
    '黃': 60, '太': 62, '仲': 64, '林': 65,
    '南': 67, '應': 69, '潢': 71, '溝': 72,
}

def jeongganbo_to_midi_and_score(text, midi_path, image_prefix):
    midi = MIDIFile(1)
    track, time = 0, 0
    midi.addTrackName(track, time, "Jeongganbo")
    midi.addTempo(track, time, 120)
    duration = 1
    volume = 100
    channel = 0

    notes = []
    for char in text:
        if char in note_mapping:
            pitch = note_mapping[char]
            midi.addNote(track, channel, pitch, time, duration, volume)
            notes.append((char, pitch))
            time += duration

    if not notes:
        return False, None

    # Save MIDI
    with open(midi_path, 'wb') as f:
        midi.writeFile(f)

    # Generate score using music21
    from music21 import stream, note

    score = stream.Score()
    part = stream.Part()
    part.insert(0, instrument.Piano())
    score.insert(0, part)
    for _, pitch in notes:
        part.append(note.Note(pitch, quarterLength=1.0))

    score.metadata = metadata.Metadata()
    score.metadata.title = "Western Score"
    score.metadata.composer = "Auto-generated"

    # macOS만 MuseScore 경로 설정
    if platform.system() == "Darwin":
        env = environment.UserSettings()
        env["musescoreDirectPNGPath"] = "/Applications/MuseScore 4.app/Contents/MacOS/mscore"

    image_file = os.path.join(OUTPUT_FOLDER, "score.png")
    score.write("musicxml.png", fp=image_file)

    return True, "output/score.png"

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
                    image_path=image_file,
                    jeongganbo_text=text
                )
            else:
                return render_template("index.html", error="⚠ No valid Jeongganbo notes found.")
        else:
            return render_template("index.html", error="Please upload a .txt file.")
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
