from music21 import stream, note

# 정간보 기호 → 서양 음계 매핑
jeongganbo_to_western = {
    "黃": "C4", "太": "D4", "仲": "E4",
    "林": "F4", "南": "G4", "應": "A4",
    "潢": "B4", "溝": "G3", "△": "rest", "-": "tie"
}

# 박자 길이 반영 함수
def get_note_length(char):
    if "一" in char:  # 8분음표
        return 0.5
    elif len(char) > 1:  # 16분음표 (기호 2개 이상이면 더 쪼개짐)
        return 0.25
    return 1.0  # 기본 4분음표

# 정간보 변환 함수
def convert_jeongganbo_to_western(jeongganbo_text):
    """정간보 데이터를 서양 음계로 변환 (박자 & 연장선 반영)"""
    western_notes = []
    prev_note = None

    for char in jeongganbo_text.split("/"):
        char = char.strip()
        note_length = get_note_length(char)

        if char in jeongganbo_to_western:
            if char == "-":
                if prev_note:  # 이전 음을 연장
                    western_notes.append((prev_note, note_length, "tie"))
            else:
                western_notes.append((jeongganbo_to_western[char], note_length, None))
                prev_note = jeongganbo_to_western[char]  # 이전 음 저장

        elif "一" in char:  # 한 박자 안에 여러 개의 음표
            base_char = char.replace("一", "").strip()
            if base_char in jeongganbo_to_western:
                western_notes.append((jeongganbo_to_western[base_char], note_length, None))
                prev_note = jeongganbo_to_western[base_char]

    return western_notes

# MIDI 변환 함수 (연장선 반영)
def save_as_midi(notes, filename="jeongganbo_output.mid"):
    """서양 음계를 MIDI 파일로 저장 (박자 & 연장선 반영)"""
    s = stream.Stream()
    prev_m21_note = None

    for n, duration, tie_flag in notes:
        if n == "rest":
            s.append(note.Rest(quarterLength=duration))
        else:
            m21_note = note.Note(n, quarterLength=duration)
            if tie_flag == "tie" and prev_m21_note:
                prev_m21_note.tie = note.Tie("start")
                m21_note.tie = note.Tie("stop")

            s.append(m21_note)
            prev_m21_note = m21_note

    s.write('midi', fp=filename)
    print(f"MIDI 파일이 생성되었습니다: {filename}")

# 실행 흐름
jeongganbo_data = """
黃 / 一太 / 黃太 / 仲 / 一林 / 仲林 / 南 / 林 / 仲太 / 黃 / 一太 / 黃太
仲 / 一 林 / 仲林 / 南林 / 仲太 / 黃太 / 仲 / 一林 / 仲 / 仲
潢 / (공백) / 潢 / 溝 / 南林 / 仲 / 南 / 林 / 仲太 / 黃 / 一太 / 黃太
"""
western_notes = convert_jeongganbo_to_western(jeongganbo_data)
save_as_midi(western_notes, "jeongganbo_output.mid")
