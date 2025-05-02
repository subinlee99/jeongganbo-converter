from flask import Flask, render_template, request, send_file, jsonify
from flask import redirect
import os
from pydub import AudioSegment
from music21 import converter, note, stream, environment, instrument, metadata
from midiutil import MIDIFile
import platform
import matplotlib
matplotlib.use("Agg")
app = Flask(__name__)

# Tell music21 to use MuseScore for rendering
environment.set('musicxmlPath', '/Applications/MuseScore 4.app/Contents/MacOS/mscore')
environment.set('musescoreDirectPNGPath', '/Applications/MuseScore 4.app/Contents/MacOS/mscore')

# Dummy playlist
playlist = [
    {
        "title": "Awesome Song",
        "album_cover": "static/albums/covers/lu.jpg",
        "audio": "static/albums/mp3s/song1.mp3",
        "sheet": "static/sheets/song1.xml"
    },
    {
        "title": "Everglow",
        "album_cover": "static/albums/covers/23232.png",
        "audio": "static/albums/mp3s/song2.mp3",
        "sheet": "static/sheets/song1.xml"
    },
    {
        "title": "A.P.T.",
        "album_cover": "static/albums/covers/rose.jpeg",
        "audio": "static/albums/mp3s/song2.mp3",
        "sheet": "static/sheets/song2.xml"
    },
    {
        "title": "Thinking Out Loud",
        "album_cover": "static/albums/covers/song4.webp",
        "audio": "static/albums/mp3s/song2.mp3",
        "sheet": "static/sheets/song2.xml"
    },
    {
        "title": "Nobody Gets Me",
        "album_cover": "static/albums/covers/SZA-SOS.webp",
        "audio": "static/albums/mp3s/song2.mp3",
        "sheet": "static/sheets/song2.xml"
    }
]


note_mapping = {
    '黃': 60, '太': 62, '仲': 64, '林': 65,
    '南': 67, '應': 69, '潢': 71, '溝': 72
}

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def image_to_jeongganbo_text(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang='kor+eng')  # use Korean OCR if available
    return text.strip()

def jeongganbo_to_midi_and_score(text, midi_path):
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

    with open(midi_path, 'wb') as f:
        midi.writeFile(f)

    # Create music21 score
    score = stream.Score()
    part = stream.Part()
    part.insert(0, instrument.Piano())
    score.insert(0, part)
    for _, pitch in notes:
        part.append(note.Note(pitch, quarterLength=1.0))

    score.metadata = metadata.Metadata()
    score.metadata.title = "Western Score"
    score.metadata.composer = "Auto-generated"

    # MuseScore path (for macOS only)
    if platform.system() == "Darwin":
        env = environment.UserSettings()
        env["musescoreDirectPNGPath"] = "/Applications/MuseScore 4.app/Contents/MacOS/mscore"

    image_output_path = os.path.join(OUTPUT_FOLDER, "score.png")
    actual_image_path = score.write("musicxml.png", fp=image_output_path)
    relative_image_path = os.path.relpath(actual_image_path, "static")

    return True, relative_image_path

def midi_to_mp3(midi_path, mp3_path):
    wav_path = midi_path.replace(".mid", ".wav")
    result = os.system(f"timidity {midi_path} -Ow -o {wav_path}")

    if not os.path.exists(wav_path):
        raise FileNotFoundError("⚠️ Failed to convert MIDI to WAV. Is Timidity installed?")

    sound = AudioSegment.from_wav(wav_path)
    sound.export(mp3_path, format="mp3")
    os.remove(wav_path)


@app.route('/')
def root():
    return redirect('/welcome')

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route("/upload_jeongganbo_text", methods=["GET", "POST"])
def upload_jeongganbo_text():
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith(".txt"):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()

            midi_path = os.path.join(OUTPUT_FOLDER, "western_from_jeongganbo.mid")
            score_image_path = os.path.join(OUTPUT_FOLDER, "western_score_from_jeongganbo.png")

            success, image_path = jeongganbo_to_midi_and_score(text, midi_path)
            if success:
                return render_template(
                    "upload_jeongganbo_text.html",
                    image_path=image_path,
                    jeongganbo_text=text
                )
            else:
                return render_template("upload_jeongganbo_text.html", error="⚠ No valid Jeongganbo notes found.")
        else:
            return render_template("upload_jeongganbo_text.html", error="Please upload a .txt file.")
    return render_template("upload_jeongganbo_text.html")

@app.route('/sheet_image')
def sheet_image():
    import uuid

    sheet_path = request.args.get("sheet")
    try:
        score = converter.parse(sheet_path)

        # Save as PDF using MuseScore 4
        filename = f"static/sheet_{uuid.uuid4().hex}.pdf"
        score.write('musicxml.pdf', fp=filename)

        return send_file(filename, mimetype='application/pdf')
    except Exception as e:
        return f"Error rendering sheet: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html', playlist=playlist)

import os

@app.route('/convert', methods=['POST'])
def convert():
    sheet_path = request.json.get("sheet")
    jeongganbo_notes = []

    if not sheet_path or not os.path.exists(sheet_path):
        return jsonify({"error": f"Invalid or missing sheet path: {sheet_path}"}), 400

    try:
        score = converter.parse(sheet_path)
        for el in score.recurse():
            if isinstance(el, note.Note):
                for k, v in note_mapping.items():
                    if el.pitch.midi == v:
                        jeongganbo_notes.append(k)
                        break
        return jsonify({"jeongganbo": jeongganbo_notes})
    except Exception as e:
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
