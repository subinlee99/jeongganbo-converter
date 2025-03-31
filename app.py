import os
import subprocess
from flask import Flask, render_template, request, send_file, url_for
from music21 import stream, note, converter

app = Flask(__name__)

# 🔹 Directories for uploads and output
UPLOAD_FOLDER = os.path.abspath("uploads")
OUTPUT_FOLDER = os.path.abspath("static/output")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 🔹 Mapping from Jeongganbo symbols to Western notation
jeongganbo_to_western = {
    "黃": "C4", "太": "D4", "仲": "E4",
    "林": "F4", "南": "G4", "應": "A4",
    "潢": "B4", "溝": "G3", "△": "rest", "-": "tie"
}

def convert_jeongganbo_to_musicxml_and_midi(filepath):
    """Convert Jeongganbo text file to MusicXML and MIDI"""
    with open(filepath, "r", encoding="utf-8") as file:
        data = file.read()

    western_notes = []
    for char in data.split():
        if char in jeongganbo_to_western:
            western_notes.append(jeongganbo_to_western[char])
        elif char.isalnum():
            print(f"🚨 Invalid character detected: {char} (excluded from conversion)")

    s = stream.Stream()
    for n in western_notes:
        if n == "rest":
            s.append(note.Rest(quarterLength=1))  # Rest as a quarter note
        else:
            new_note = note.Note(n)
            new_note.quarterLength = 1  # All notes set as quarter notes
            s.append(new_note)

    musicxml_path = os.path.join(OUTPUT_FOLDER, "output.musicxml")
    midi_path = os.path.join(OUTPUT_FOLDER, "output.mid")

    s.write('musicxml', fp=musicxml_path)
    s.write('midi', fp=midi_path)

    return musicxml_path, midi_path

def generate_sheet_music_pdf(musicxml_path):
    """Use MuseScore 4 to convert MusicXML to PDF"""
    output_pdf_path = os.path.join(OUTPUT_FOLDER, "output.pdf")

    # 🔍 Find the correct MuseScore path
    musescore_paths = [
        "/Applications/MuseScore 4.app/Contents/MacOS/mscore",
        "/Applications/MuseScore 4.app/Contents/MacOS/MuseScore4"
    ]
    musescore_path = None

    for path in musescore_paths:
        if os.path.exists(path):
            musescore_path = path
            break

    if not musescore_path:
        print("🚨 MuseScore executable not found.")
        return None

    try:
        # 🚀 Set proper QT environment variables
        env = os.environ.copy()
        env["QT_QPA_PLATFORM"] = "cocoa"  # Use cocoa instead of offscreen
        env["QT_QPA_PLATFORM_PLUGIN_PATH"] = "/Applications/MuseScore 4.app/Contents/PlugIns/platforms"

        result = subprocess.run([musescore_path, "-o", output_pdf_path, musicxml_path], 
                                env=env, capture_output=True, text=True, check=True)
        print("✅ MuseScore Execution Output:", result.stdout)
        print("🚨 MuseScore Error Messages:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"🚨 MuseScore conversion failed (Error Code {e.returncode}): {e.stderr}")
        return None
    except Exception as e:
        print(f"🚨 MuseScore execution error: {e}")
        return None

    if not os.path.exists(output_pdf_path):
        print("🚨 MuseScore failed to generate a PDF file!")
        return None

    return output_pdf_path

@app.route("/", methods=["GET", "POST"])
def index():
    pdf_path, midi_path = None, None
    if request.method == "POST":
        print("✅ POST request received")
        if "file" not in request.files:
            print("❌ No file uploaded")
            return "No file uploaded.", 400

        file = request.files["file"]
        if file.filename == "":
            print("❌ No file selected")
            return "No file selected.", 400

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)
        print(f"✅ File successfully saved: {filepath}")

        # Process Jeongganbo conversion
        musicxml_path, midi_path = convert_jeongganbo_to_musicxml_and_midi(filepath)
        pdf_path = generate_sheet_music_pdf(musicxml_path)

        if not pdf_path:
            return "Sheet music conversion failed (check MuseScore execution).", 500

    return render_template("index.html", pdf_path=pdf_path, midi_path=midi_path)

@app.route("/download/<filename>")
def download_file(filename):
    """Allow users to download generated files"""
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found.", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
