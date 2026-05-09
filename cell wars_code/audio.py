import pygame, math
import numpy as np

_sounds: dict = {}
_ready = False
_muted = False


def _make_beep(freq, ms, vol=0.4, shape="sine",decay=6.0):
    sr = 44100
    n = int(sr * ms / 1000)
    t = np.linspace(0, ms/1000,n,endpoint=False)
    if shape == "square":
        raw = np.sign(np.sin(2*math.pi*freq*t))
    elif shape == "sawtooth":
        raw = 2*(t*freq - np.floor(t*freq+0.5))
    else:
        raw = np.sin(2*math.pi*freq*t)
    env  = np.exp(-decay * t / (ms/1000))
    data = (raw * env * vol * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack((data, data)))


def audio_init():
    global _sounds, _ready
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        _sounds = {"shoot":_make_beep(880,60,0.25,"sine",8),"kill": _make_beep(440,120,0.35,"square",5),
            "player_hit": _make_beep(180,200,0.45,"square",4),"boss_hit":_make_beep(300,100,0.40,"sine",3),
            "boss_kill":_make_beep(220,500,0.55,"sawtooth",2),"wave_clear": _make_beep(660,300, 0.40,"sine",3),
            "powerup":_make_beep(1046,150,0.35,"sine",5),"combo":_make_beep(880,200,0.30,"sine",4),
            "zone":_make_beep(330,600,0.45,"sine",2)}
        _ready = True
    except Exception as e:
        print(f"[Audio] disabled: {e}")
        _ready = False


def audio_play(name):
    if not _ready or _muted:
        return
    snd = _sounds.get(name)
    if snd is not None:
        try:
            snd.play()
        except Exception:
            pass


def audio_toggle_mute() -> bool:
    global _muted
    _muted = not _muted
    return _muted


def audio_is_muted() -> bool:
    return _muted
