type Tone = {
  frequency: number;
  start: number;
  duration: number;
  gain: number;
};

let audioContext: AudioContext | null = null;
let incomingCallTimer: number | null = null;

function getAudioContext() {
  const AudioContextCtor = window.AudioContext ?? window.webkitAudioContext;
  if (!AudioContextCtor) {
    return null;
  }
  audioContext ??= new AudioContextCtor();
  return audioContext;
}

function playTones(tones: Tone[]) {
  const context = getAudioContext();
  if (!context) {
    return;
  }
  context.resume().catch(() => undefined);
  const now = context.currentTime;
  for (const tone of tones) {
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(tone.frequency, now + tone.start);
    gain.gain.setValueAtTime(0, now + tone.start);
    gain.gain.linearRampToValueAtTime(tone.gain, now + tone.start + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.001, now + tone.start + tone.duration);
    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.start(now + tone.start);
    oscillator.stop(now + tone.start + tone.duration + 0.02);
  }
}

export function playIncomingMessageSound() {
  playTones([
    { frequency: 880, start: 0, duration: 0.08, gain: 0.08 },
    { frequency: 1175, start: 0.09, duration: 0.11, gain: 0.07 }
  ]);
}

export function playIncomingCallSound() {
  playTones([
    { frequency: 660, start: 0, duration: 0.16, gain: 0.08 },
    { frequency: 880, start: 0.18, duration: 0.16, gain: 0.08 },
    { frequency: 660, start: 0.42, duration: 0.16, gain: 0.07 },
    { frequency: 880, start: 0.6, duration: 0.18, gain: 0.07 }
  ]);
}

export function startIncomingCallRingtone() {
  stopIncomingCallRingtone();
  playIncomingCallSound();
  incomingCallTimer = window.setInterval(playIncomingCallSound, 1350);
  return stopIncomingCallRingtone;
}

export function stopIncomingCallRingtone() {
  if (incomingCallTimer !== null) {
    window.clearInterval(incomingCallTimer);
    incomingCallTimer = null;
  }
}
