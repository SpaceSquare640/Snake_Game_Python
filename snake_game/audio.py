"""Procedural sound: a tiny synth (no audio files, no numpy)."""
import array
import math

import pygame


def _tone(freq, ms, vol=0.35, sr=22050, shape="square"):
    """Build a 16-bit mono sample buffer for a single enveloped tone."""
    n = max(1, int(sr * ms / 1000))
    buf = array.array("h")
    attack = sr * 0.005
    release = sr * 0.03
    for i in range(n):
        t = i / sr
        if shape == "square":
            s = vol if math.sin(2 * math.pi * freq * t) >= 0 else -vol
        else:
            s = vol * math.sin(2 * math.pi * freq * t)
        env = min(1.0, i / attack) * min(1.0, (n - i) / release)
        buf.append(int(max(-1.0, min(1.0, s * env)) * 32767))
    return buf


def _sequence(notes, sr=22050, vol=0.22, shape="sine"):
    """Concatenate (freq, ms) notes into one buffer (freq 0 = rest)."""
    out = array.array("h")
    for freq, ms in notes:
        if freq <= 0:
            out.extend(array.array("h", [0]) * int(sr * ms / 1000))
        else:
            out.extend(_tone(freq, ms, vol=vol, sr=sr, shape=shape))
    return out


class SoundManager:
    """Synthesizes effect and music buffers at startup; respects settings."""

    SR = 22050

    def __init__(self, profile):
        self.profile = profile
        self.ok = False
        self.sounds = {}
        self.music = None
        self.music_channel = None
        try:
            pygame.mixer.quit()
            pygame.mixer.init(frequency=self.SR, size=-16, channels=1, buffer=512)
            self._build()
            self.ok = True
        except Exception:
            self.ok = False
        if self.ok and self.profile.music:
            self.start_music()

    def _snd(self, buf):
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _build(self):
        self.sounds = {
            "eat": self._snd(_tone(880, 70, vol=0.4)),
            "select": self._snd(_tone(520, 45, vol=0.3)),
            "crash": self._snd(_tone(150, 240, vol=0.45, shape="square")),
            "win": self._snd(_sequence([(523, 90), (659, 90), (784, 90), (1046, 160)],
                                       vol=0.35, shape="square")),
        }
        # A gentle looping melody for background music.
        loop = [
            (392, 220), (523, 220), (659, 220), (523, 220),
            (440, 220), (587, 220), (440, 220), (0, 120),
            (349, 220), (523, 220), (659, 220), (784, 220),
            (659, 220), (523, 220), (440, 220), (0, 260),
        ]
        self.music = self._snd(_sequence(loop, vol=0.12, shape="sine"))

    def play(self, name):
        if self.ok and self.profile.sound and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass

    def start_music(self):
        if not self.ok or not self.music:
            return
        try:
            self.music_channel = self.music.play(loops=-1)
        except Exception:
            self.music_channel = None

    def stop_music(self):
        if self.music_channel:
            try:
                self.music_channel.stop()
            except Exception:
                pass
            self.music_channel = None

    def set_music(self, on):
        if on:
            self.start_music()
        else:
            self.stop_music()
