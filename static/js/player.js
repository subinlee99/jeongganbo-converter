// static/js/player.js

const AudioContextFunc = window.AudioContext || window.webkitAudioContext;
const audioContext = new AudioContextFunc();
const player = new WebAudioFontPlayer();

const instrumentId = "_tone_0000_AcousticGrandPiano";
const soundFontURL = "https://surikov.github.io/webaudiofontdata/sound/12835_0_AcousticGrandPiano_sf2_file.js";

// 악기 사운드폰트 로드
const script = document.createElement('script');
script.src = soundFontURL;
script.onload = () => {
  player.loader.decodeAfterLoading(audioContext, window[instrumentId]);
  document.getElementById("playBtn").disabled = false;
  console.log("🎹 Instrument loaded!");
};
document.head.appendChild(script);

function playMIDI() {
  fetch("/static/output/output.mid")
    .then(response => response.arrayBuffer())
    .then(buffer => {
      const midiFile = player.loader.parseMidi(buffer);
      player.queueMidiPlayer(audioContext, midiFile, 0, window[instrumentId]);
      console.log("▶ Playing MIDI");
    })
    .catch(err => console.error("🚨 Error playing MIDI:", err));
}
