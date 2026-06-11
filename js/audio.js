/* Sound — WebAudio oscillator synth (no asset files). */

export class SoundManager {
  constructor(profile) {
    this.profile = profile;
    this.ctx = null;
    this.musicTimer = null;
    this.muted = false; // driven by the CrazyGames portal's mute toggle
    try {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    } catch (e) { this.ctx = null; }
  }

  // Honour the platform mute switch: silence everything, restoring music if
  // the player had it on when they un-mute.
  setMuted(on) {
    this.muted = !!on;
    if (this.muted) this.stopMusic();
    else if (this.profile.music) this.startMusic();
  }
  resume() {
    if (this.ctx && this.ctx.state === "suspended") this.ctx.resume();
    if (this.profile.music && !this.muted && !this.musicTimer) this.startMusic();
  }
  _beep(freq, ms, type, vol) {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const g = this.ctx.createGain();
    osc.type = type; osc.frequency.value = freq;
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(vol, t + 0.005);
    g.gain.exponentialRampToValueAtTime(0.0001, t + ms / 1000);
    osc.connect(g); g.connect(this.ctx.destination);
    osc.start(t); osc.stop(t + ms / 1000 + 0.02);
  }
  play(name) {
    if (!this.ctx || !this.profile.sound || this.muted) return;
    if (name === "eat") this._beep(880, 70, "square", 0.18);
    else if (name === "select") this._beep(520, 45, "square", 0.13);
    else if (name === "crash") this._beep(150, 240, "square", 0.2);
    else if (name === "win") {
      [523, 659, 784, 1046].forEach((f, i) =>
        setTimeout(() => this._beep(f, 150, "square", 0.18), i * 90));
    }
  }
  startMusic() {
    if (!this.ctx || this.muted) return;
    this.stopMusic();
    const notes = [392, 523, 659, 523, 440, 587, 440, 0,
                   349, 523, 659, 784, 659, 523, 440, 0];
    let i = 0;
    this.musicTimer = setInterval(() => {
      const f = notes[i % notes.length]; i++;
      if (f > 0) this._beep(f, 200, "sine", 0.06);
    }, 230);
  }
  stopMusic() {
    if (this.musicTimer) { clearInterval(this.musicTimer); this.musicTimer = null; }
  }
  setMusic(on) { if (on) this.startMusic(); else this.stopMusic(); }
}
