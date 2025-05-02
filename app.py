from flask import Flask, render_template, request
from midiutil import MIDIFile
from pydub import AudioSegment
from music21 import converter, instrument, metadata, environment, stream, note
import matplotlib
matplotlib.use("Agg")
import os
import platform
#import openai

#openai.api_key = os.getenv("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")  # Make sure to set your key in the environment

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

            success, image_path = jeongganbo_to_midi_and_score(text, midi_path)
            if success:
                midi_to_mp3(midi_path, mp3_path)
                return render_template(
                    "index.html",
                    mp3_generated=True,
                    image_path=image_path,
                    jeongganbo_text=text
                )
            else:
                return render_template("index.html", error="⚠ No valid Jeongganbo notes found.")
        else:
            return render_template("index.html", error="Please upload a .txt file.")
    return render_template("index.html")


from openai import OpenAI
client = OpenAI(api_key="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")
response = client.models.list()
print("✅ OpenAI client is working!")
@app.route("/convert_gugak", methods=["POST"])
def convert_gugak():
    midi_path = os.path.join(OUTPUT_FOLDER, "jeongganbo.mid")
    mp3_path = os.path.join(OUTPUT_FOLDER, "jeongganbo_gugak.mp3")

    if not os.path.exists(midi_path):
        return render_template("index.html", error="MIDI file not found.")

    prompt = """
You are a music composer trained in Korean traditional music (Gugak). 
Take the following Western music elements and convert them into a Gugak-style arrangement using instruments like Gayageum, Daegeum, or Haegeum.

Input MIDI: Jeongganbo.mid
Instrumentation: Piano
Tempo: 120 bpm

Give suggestions on which instruments to substitute and what modifications to apply.
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    instructions = response.choices[0].message.content.strip()

    with open(os.path.join(OUTPUT_FOLDER, "gugak_instructions.txt"), "w") as f:
        f.write(instructions)

    original_mp3 = os.path.join(OUTPUT_FOLDER, "jeongganbo.mp3")
    if os.path.exists(original_mp3):
        from shutil import copyfile
        copyfile(original_mp3, mp3_path)

    txt_files = sorted(
        [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".txt")],
        key=lambda x: os.path.getmtime(os.path.join(UPLOAD_FOLDER, x)),
        reverse=True
    )
    text = ""
    if txt_files:
        with open(os.path.join(UPLOAD_FOLDER, txt_files[0]), "r", encoding="utf-8") as f:
            text = f.read()

    return render_template(
        "index.html",
        mp3_generated=True,
        gugak_generated=True,
        image_path="output/score.png",
        gugak_instructions=instructions,
        jeongganbo_text=text
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
