from flask import Flask, render_template, request, send_file, jsonify, redirect
import os
import platform
import uuid
from pydub import AudioSegment
from music21 import converter, note, stream, environment, instrument, metadata
from midiutil import MIDIFile
import matplotlib
from PIL import Image
import pytesseract



matplotlib.use("Agg")

app = Flask(__name__)

# Configure paths
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Configure MuseScore
environment.set('musicxmlPath', '/Applications/MuseScore 4.app/Contents/MacOS/mscore')
environment.set('musescoreDirectPNGPath', '/Applications/MuseScore 4.app/Contents/MacOS/mscore')

# Playlist
songs = [
  {
    "title": "Super Shy",
    "album_cover": "static/albums/covers/Super Shy.jpg",
    "audio": "static/albums/mp3s/Super Shy.mp3",
    "sheet": "static/sheets/Super Shy.xml",
    "album_cover_gugak": "static/albums/covers/Super Shy_G.png",
    "audio_gugak": "static/albums/mp3s/Super Shy_G.mp3"
  },
  {
    "title": "Supernova",
    "album_cover": "static/albums/covers/Supernova.jpg",
    "audio": "static/albums/mp3s/Supernova.mp3",
    "sheet": "static/sheets/Supernova.xml",
    "album_cover_gugak": "static/albums/covers/Supernova_G.png",
    "audio_gugak": "static/albums/mp3s/Supernova_G.mp3"
  },
  {
    "title": "suzume",
    "album_cover": "static/albums/covers/suzume.jpg",
    "audio": "static/albums/mp3s/suzume.mp3",
    "sheet": "static/sheets/suzume.xml",
    "album_cover_gugak": "static/albums/covers/suzume_G.png",
    "audio_gugak": "static/albums/mp3s/suzume_G.mp3"
  },
  {
    "title": "The Simpsons",
    "album_cover": "static/albums/covers/The Simpsons.jpg",
    "audio": "static/albums/mp3s/The Simpsons.mp3",
    "sheet": "static/sheets/The Simpsons.xml",
    "album_cover_gugak": "static/albums/covers/The Simpsons_G.png",
    "audio_gugak": "static/albums/mp3s/The Simpsons_G.mp3"
  },
  {
    "title": "Viva La Vida",
    "album_cover": "static/albums/covers/Viva La Vida.jpg",
    "audio": "static/albums/mp3s/Viva La Vida.mp3",
    "sheet": "static/sheets/Viva La Vida.xml",
    "album_cover_gugak": "static/albums/covers/Viva La Vida_G.png",
    "audio_gugak": "static/albums/mp3s/Viva La Vida_G.mp3"
  },
  {
    "title": "APT",
    "album_cover": "static/albums/covers/APT.jpg",
    "audio": "static/albums/mp3s/APT.mp3",
    "sheet": "static/sheets/APT.xml",
    "album_cover_gugak": "static/albums/covers/APT_G.png",
    "audio_gugak": "static/albums/mp3s/APT_G.mp3"
  },
  {
    "title": "Attention",
    "album_cover": "static/albums/covers/Attention.jpg",
    "audio": "static/albums/mp3s/Attention.mp3",
    "sheet": "static/sheets/Attention.xml",
    "album_cover_gugak": "static/albums/covers/Attention_G.png",
    "audio_gugak": "static/albums/mp3s/Attention_G.mp3"
  },
  {
    "title": "Beethoven",
    "album_cover": "static/albums/covers/Beethoven.jpg",
    "audio": "static/albums/mp3s/Beethoven.mp3",
    "sheet": "static/sheets/Beethoven.xml",
    "album_cover_gugak": "static/albums/covers/Beethoven_G.png",
    "audio_gugak": "static/albums/mp3s/Beethoven_G.mp3"
  },
  {
    "title": "Butter",
    "album_cover": "static/albums/covers/Butter.jpg",
    "audio": "static/albums/mp3s/Butter.mp3",
    "sheet": "static/sheets/song1.xml",
    "album_cover_gugak": "static/albums/covers/Butter_G.png",
    "audio_gugak": "static/albums/mp3s/Butter_G.mp3"
  },
  {
    "title": "Howl_s Moving Castle",
    "album_cover": "static/albums/covers/Howl_s Moving Castle.jpeg",
    "audio": "static/albums/mp3s/Howl_s Moving Castle.mp3",
    "sheet": "static/sheets/Howl_s Moving Castle.xml",
    "album_cover_gugak": "static/albums/covers/Howl_s Moving Castle_G.png",
    "audio_gugak": "static/albums/mp3s/Howl_s Moving Castle_G.mp3"
  },
  {
    "title": "Love Dive",
    "album_cover": "static/albums/covers/Love Dive.webp",
    "audio": "static/albums/mp3s/Love Dive.mp3",
    "sheet": "static/sheets/Love Dive.xml",
    "album_cover_gugak": "static/albums/covers/Love Dive_G.png",
    "audio_gugak": "static/albums/mp3s/Love Dive_G.mp3"
  },
  {
    "title": "Shape Of You",
    "album_cover": "static/albums/covers/Shape Of You.jpg",
    "audio": "static/albums/mp3s/Shape Of You.mp3",
    "sheet": "static/sheets/Shape Of You.xml",
    "album_cover_gugak": "static/albums/covers/Shape Of You_G.png",
    "audio_gugak": "static/albums/mp3s/Shape Of You_G.mp3"
  },
  {
    "title": "Shut Down",
    "album_cover": "static/albums/covers/Shut Down.jpg",
    "audio": "static/albums/mp3s/Shut Down.mp3",
    "sheet": "static/sheets/Shut Down.xml",
    "album_cover_gugak": "static/albums/covers/Shut Down_G.png",
    "audio_gugak": "static/albums/mp3s/Shut Down_G.mp3"
  }
]


# Jeongganbo note mapping
note_mapping = {
    '黃': 60, '太': 62, '仲': 64, '林': 65,
    '南': 67, '應': 69, '潢': 71, '溝': 72
}
reverse_mapping = {v: k for k, v in note_mapping.items()}
smufl_glyphs = {
    60: "\U0001D15F",  # C4 quarter note
    62: "\U0001D160",  # D4 quarter note
    64: "\U0001D161",  # E4 quarter note
    65: "\U0001D162",  # F4 quarter note
    67: "\U0001D163",  # G4 quarter note
    69: "\U0001D164",  # A4 quarter note
    71: "\U0001D165",  # B4 quarter note
    72: "\U0001D15F"   # C5 (loop back for demo)
}
@app.route('/')
def root():
    return redirect('/welcome')

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/select')
def select():
    return render_template('select.html', playlist=songs)

@app.route('/player')
def player():
    sheet = request.args.get("sheet")
    audio = request.args.get("audio")
    cover = request.args.get("cover")
    title = request.args.get("title")
    cover_gugak = request.args.get("album_cover_gugak")
    audio_gugak = request.args.get("audio_gugak")

    sheet_image = None

    if sheet and os.path.exists(sheet):
        try:
            score = converter.parse(sheet)
            img_path = os.path.join(OUTPUT_FOLDER, f"sheet_{uuid.uuid4().hex}.png")
            score.write("musicxml.png", fp=img_path)
            sheet_image = os.path.relpath(img_path, "static")
        except Exception as e:
            print("⚠ Failed to render MusicXML to image:", e)
    else:
        print(f"⚠ Provided sheet path does not exist: {sheet}")

    return render_template("index.html", title=title, audio=audio, cover=cover, sheet_image=sheet_image, sheet=sheet, cover_gugak=cover_gugak, audio_gugak=audio_gugak)
@app.route('/gugakify')
def gugakify():
    sheet = request.args.get("sheet")
    cover = request.args.get("cover")
    title = request.args.get("title")
    audio = request.args.get("audio")
    audio_gugak = request.args.get("audio_gugak")
    cover_gugak = request.args.get("album_cover_gugak")

    jeongganbo_text = []
    western_jeongganbo_pairs = []
    svg_path = None

    try:
        # Load the MusicXML file
        parsed = converter.parse(sheet)

        # Save SVG rendering
        svg_path = os.path.join(OUTPUT_FOLDER, f"svg_{uuid.uuid4().hex}.svg")
        parsed.write('musicxml.svg', fp=svg_path)
        svg_path = os.path.relpath(svg_path, "static")

        # Build Jeongganbo ↔ Western pairs
        for el in parsed.recurse():
            if isinstance(el, note.Note):
                midi = el.pitch.midi
                if midi in reverse_mapping:
                    symbol = reverse_mapping[midi]
                    glyph = smufl_glyphs.get(midi, el.nameWithOctave)
                    western_jeongganbo_pairs.append({
                        "western": glyph,
                        "jeongganbo": symbol
                    })
    except Exception as e:
        print(f"⚠ Error parsing sheet: {e}")
        return "No valid Western ↔ Jeongganbo notes found in this file.", 400

    if not western_jeongganbo_pairs:
        return "No valid Western ↔ Jeongganbo notes found in this file.", 400

    # Generate Gugak-style audio
    midi_path = os.path.join(OUTPUT_FOLDER, f"gugak_{uuid.uuid4().hex}.mid")
    success, gugak_img = jeongganbo_to_midi_and_score("".join([p['jeongganbo'] for p in western_jeongganbo_pairs]), midi_path)

    gugak_mp3_path = None
    if success:
        try:
            mp3_path = os.path.join(OUTPUT_FOLDER, f"gugak_output_{uuid.uuid4().hex}.mp3")
            midi_to_mp3(midi_path, mp3_path)
            gugak_mp3_path = mp3_path.replace("static/", "")
        except Exception as e:
            print("MP3 conversion failed:", e)

    return render_template("gugakify.html",
                           title=title,
                           cover=cover,
                           audio=audio,
                           svg_sheet=svg_path,
                           jeongganbo=gugak_img,
                           jeongganbo_text="".join([p['jeongganbo'] for p in western_jeongganbo_pairs]),
                           gugak_audio=audio_gugak,
                           cover_gugak=cover_gugak,
                           western_jeongganbo_pairs=western_jeongganbo_pairs)



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
            success, image_path = jeongganbo_to_midi_and_score(text, midi_path)

            if success:
                return render_template("upload_jeongganbo_text.html", image_path=image_path, jeongganbo_text=text)
            else:
                return render_template("upload_jeongganbo_text.html", error="⚠ No valid Jeongganbo notes found.")
        return render_template("upload_jeongganbo_text.html", error="Please upload a .txt file.")
    return render_template("upload_jeongganbo_text.html")

@app.route('/sheet_image')
def sheet_image():
    sheet_path = request.args.get("sheet")
    try:
        score = converter.parse(sheet_path)
        filename = f"static/sheet_{uuid.uuid4().hex}.pdf"
        score.write('musicxml.pdf', fp=filename)
        return send_file(filename, mimetype='application/pdf')
    except Exception as e:
        return f"Error rendering sheet: {str(e)}", 500

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

# Helpers
def image_to_jeongganbo_text(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang='kor+eng')
    return text.strip()

def jeongganbo_to_midi_and_score(text, midi_path):
    midi = MIDIFile(1)
    track, time = 0, 0
    midi.addTrackName(track, time, "Jeongganbo")
    midi.addTempo(track, time, 120)

    duration, volume, channel = 1, 100, 0
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

    score = stream.Score()
    part = stream.Part()
    part.insert(0, instrument.Piano())
    score.insert(0, part)
    for _, pitch in notes:
        part.append(note.Note(pitch, quarterLength=1.0))

    score.metadata = metadata.Metadata()
    score.metadata.title = "Western Score"
    score.metadata.composer = "Auto-generated"

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

if __name__ == '__main__':
    app.run(debug=True)