"""
Audio Manager module for Pi Arcade OS.

Provides a unified audio engine for both Desktop Mode (programmatic PCM sound synthesis via pygame.mixer)
and Raspberry Pi Mode (passive GPIO buzzer output on BCM 12).
Supports volume control, channel scaling, muting, non-blocking playback, and hardware isolation fallbacks.
Supports Python 3.9+ typing.
"""

import array
import logging
import math
import threading
import time
from typing import Dict, List, Optional, Tuple
import pygame

from src.config import (
    SoundType,
    GPIO_PIN_BUZZER,
    DEFAULT_VOLUME,
    AUDIO_SAMPLE_RATE,
)

logger = logging.getLogger(__name__)

# Optional import of gpiozero for Raspberry Pi hardware
try:
    from gpiozero import TonalBuzzer, Buzzer
    from gpiozero.tones import Tone
    BUZZER_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.info(f"Buzzer hardware package unavailable ({e}). Audio running in Desktop/Fallback mode.")
    TonalBuzzer = None
    Buzzer = None
    Tone = None
    BUZZER_AVAILABLE = False


class AudioManager:
    """Unified audio engine for desktop PCM synthesis and Raspberry Pi GPIO buzzer tones."""

    def __init__(self, enable_audio: bool = True, volume: float = DEFAULT_VOLUME) -> None:
        """
        Initializes the AudioManager.

        Args:
            enable_audio: If True, attempts hardware/mixer initialization.
            volume: Initial volume level between 0.0 and 1.0.
        """
        self._enabled: bool = enable_audio
        self._master_volume: float = max(0.0, min(1.0, volume))
        self._effects_volume: float = 1.0
        self._music_volume: float = 1.0
        self._muted: bool = False

        self._mixer_initialized: bool = False
        self._buzzer_initialized: bool = False
        self._buzzer: Optional[object] = None
        self._is_tonal: bool = False

        # Pre-synthesized Pygame Sound objects for desktop mode
        self._sounds: Dict[SoundType, pygame.mixer.Sound] = {}

        if enable_audio:
            self._init_audio_hardware()

    def _init_audio_hardware(self) -> None:
        """Initializes Pygame mixer for desktop mode or GPIO buzzer for Pi mode."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=AUDIO_SAMPLE_RATE, size=-16, channels=1, buffer=512)
            self._mixer_initialized = True
            self._synthesize_all_sounds()
            logger.info("Desktop PCM Audio Engine initialized via pygame.mixer.")
        except Exception as e:
            logger.warning(f"Pygame mixer initialization failed ({e}). Desktop audio disabled.")
            self._mixer_initialized = False

        if BUZZER_AVAILABLE:
            try:
                self._buzzer = TonalBuzzer(GPIO_PIN_BUZZER)
                self._is_tonal = True
                self._buzzer_initialized = True
                logger.info(f"Tonal Buzzer initialized on BCM GPIO{GPIO_PIN_BUZZER}.")
            except Exception:
                try:
                    self._buzzer = Buzzer(GPIO_PIN_BUZZER)
                    self._is_tonal = False
                    self._buzzer_initialized = True
                    logger.info(f"Standard Buzzer initialized on BCM GPIO{GPIO_PIN_BUZZER}.")
                except Exception as ex:
                    logger.warning(f"Failed to initialize buzzer hardware ({ex}).")
                    self._buzzer = None
                    self._buzzer_initialized = False

    def _synthesize_pcm_wave(
        self,
        frequencies: List[Tuple[float, float]],
        wave_type: str = "sine",
        fade_out: bool = True,
    ) -> Optional[pygame.mixer.Sound]:
        """Synthesizes a 16-bit PCM mono audio buffer using standard library array."""
        if not self._mixer_initialized:
            return None

        sample_rate = AUDIO_SAMPLE_RATE
        max_amplitude = 28000

        pcm_samples = array.array('h')
        phase = 0.0

        for freq, duration in frequencies:
            num_samples = int(sample_rate * duration)
            if num_samples <= 0:
                continue

            phase_step = (2.0 * math.pi * freq) / sample_rate

            for i in range(num_samples):
                if wave_type == "square":
                    val = max_amplitude if math.sin(phase) >= 0 else -max_amplitude
                else:
                    val = int(max_amplitude * math.sin(phase))

                envelope = 1.0
                if fade_out and num_samples > 1:
                    envelope = 1.0 - (i / float(num_samples))

                scaled_val = int(val * envelope)
                scaled_val = max(-32768, min(32767, scaled_val))
                pcm_samples.append(scaled_val)

                phase += phase_step
                if phase > 2.0 * math.pi:
                    phase -= 2.0 * math.pi

        try:
            sound = pygame.mixer.Sound(buffer=pcm_samples.tobytes())
            sound.set_volume(self._get_effective_volume())
            return sound
        except Exception as e:
            logger.debug(f"Failed to create Sound object: {e}")
            return None

    def _synthesize_sweep_wave(
        self, start_freq: float, end_freq: float, duration: float
    ) -> Optional[pygame.mixer.Sound]:
        """Synthesizes a smooth frequency sweep PCM buffer."""
        if not self._mixer_initialized:
            return None

        sample_rate = AUDIO_SAMPLE_RATE
        max_amplitude = 28000
        num_samples = int(sample_rate * duration)
        pcm_samples = array.array('h')
        phase = 0.0

        for i in range(num_samples):
            progress = i / float(num_samples)
            current_freq = start_freq + progress * (end_freq - start_freq)
            phase_step = (2.0 * math.pi * current_freq) / sample_rate

            val = int(max_amplitude * math.sin(phase) * (1.0 - progress))
            val = max(-32768, min(32767, val))
            pcm_samples.append(val)

            phase += phase_step
            if phase > 2.0 * math.pi:
                phase -= 2.0 * math.pi

        try:
            sound = pygame.mixer.Sound(buffer=pcm_samples.tobytes())
            sound.set_volume(self._get_effective_volume())
            return sound
        except Exception as e:
            logger.debug(f"Failed to create sweep Sound object: {e}")
            return None

    def _synthesize_all_sounds(self) -> None:
        """Pre-synthesizes all desktop sound effects."""
        if not self._mixer_initialized:
            return

        self._sounds[SoundType.MENU_MOVE] = self._synthesize_pcm_wave([(440.0, 0.04)])
        self._sounds[SoundType.MENU_SELECT] = self._synthesize_pcm_wave(
            [(523.25, 0.04), (659.25, 0.04), (783.99, 0.08)]
        )
        self._sounds[SoundType.ERROR] = self._synthesize_pcm_wave(
            [(150.0, 0.06), (120.0, 0.08)], wave_type="square"
        )
        self._sounds[SoundType.SNAKE_EAT] = self._synthesize_sweep_wave(400.0, 800.0, 0.08)
        self._sounds[SoundType.SNAKE_TURN] = self._synthesize_pcm_wave([(600.0, 0.02)])
        self._sounds[SoundType.GAME_OVER] = self._synthesize_pcm_wave(
            [(400.0, 0.08), (300.0, 0.08), (200.0, 0.15)]
        )
        self._sounds[SoundType.HIGH_SCORE] = self._synthesize_pcm_wave(
            [(523.25, 0.06), (659.25, 0.06), (783.99, 0.06), (1046.50, 0.18)]
        )
        self._sounds[SoundType.STARTUP_JINGLE] = self._synthesize_pcm_wave(
            [(440.0, 0.06), (554.37, 0.06), (659.25, 0.06), (880.0, 0.18)]
        )

        # Pre-synthesize Pong sound effects
        self._sounds[SoundType.PADDLE_HIT] = self._synthesize_pcm_wave([(480.0, 0.03)], wave_type="square")
        self._sounds[SoundType.WALL_BOUNCE] = self._synthesize_pcm_wave([(320.0, 0.03)])
        self._sounds[SoundType.POINT_SCORED] = self._synthesize_pcm_wave([(523.25, 0.05), (783.99, 0.08)])
        self._sounds[SoundType.MATCH_START] = self._synthesize_pcm_wave([(440.0, 0.05), (660.0, 0.08)])
        self._sounds[SoundType.PAUSE] = self._synthesize_pcm_wave([(350.0, 0.04), (250.0, 0.04)])
        self._sounds[SoundType.VICTORY] = self._synthesize_pcm_wave(
            [(523.25, 0.08), (659.25, 0.08), (783.99, 0.08), (1046.50, 0.20)]
        )
        self._sounds[SoundType.DEFEAT] = self._synthesize_pcm_wave(
            [(300.0, 0.10), (220.0, 0.10), (150.0, 0.20)], wave_type="square"
        )

    def _get_effective_volume(self) -> float:
        """Returns effective volume considering mute status and channel multipliers."""
        if self._muted or not self._enabled:
            return 0.0
        return self._master_volume * self._effects_volume

    def set_volume(self, volume: float) -> None:
        """Sets master volume level."""
        self._master_volume = max(0.0, min(1.0, float(volume)))
        self._apply_volume_to_sounds()

    def set_channel_volumes(self, master: float, effects: float, music: float) -> None:
        """Sets master, effects, and music volume channels simultaneously."""
        self._master_volume = max(0.0, min(1.0, float(master)))
        self._effects_volume = max(0.0, min(1.0, float(effects)))
        self._music_volume = max(0.0, min(1.0, float(music)))
        self._apply_volume_to_sounds()

    def _apply_volume_to_sounds(self) -> None:
        """Updates sound volumes across active mixer sounds."""
        effective_vol = self._get_effective_volume()
        if self._mixer_initialized:
            for sound in self._sounds.values():
                if sound:
                    sound.set_volume(effective_vol)

    def mute(self) -> None:
        """Mutes all audio output."""
        if not self._muted:
            self._muted = True
            self._apply_volume_to_sounds()

    def unmute(self) -> None:
        """Unmutes audio output and restores previous volume."""
        if self._muted:
            self._muted = False
            self._apply_volume_to_sounds()

    def is_muted(self) -> bool:
        """Returns True if audio is currently muted."""
        return self._muted

    @property
    def volume(self) -> float:
        """Returns the master volume level."""
        return self._master_volume

    @property
    def is_audio_enabled(self) -> bool:
        """Returns True if audio engine or hardware is active."""
        return self._enabled and (self._mixer_initialized or self._buzzer_initialized)

    def stop_all(self) -> None:
        """Stops all active audio playback on mixer and buzzer."""
        if self._mixer_initialized:
            try:
                pygame.mixer.stop()
            except Exception as e:
                logger.debug(f"Error stopping mixer audio: {e}")

        if self._buzzer_initialized and self._buzzer:
            try:
                if self._is_tonal:
                    self._buzzer.stop()
                else:
                    self._buzzer.off()
            except Exception as e:
                logger.debug(f"Error stopping buzzer audio: {e}")

    def play(self, sound_type: SoundType) -> None:
        """Plays the specified sound effect non-blocking."""
        if not self._enabled or self._muted or self._get_effective_volume() <= 0.0:
            return

        if self._mixer_initialized and sound_type in self._sounds:
            sound = self._sounds[sound_type]
            if sound:
                try:
                    sound.set_volume(self._get_effective_volume())
                    sound.play()
                    return
                except Exception as e:
                    logger.debug(f"Error playing sound on mixer: {e}")

        if self._buzzer_initialized:
            threading.Thread(target=self._play_buzzer_sequence, args=(sound_type,), daemon=True).start()
            return

    def _play_buzzer_sequence(self, sound_type: SoundType) -> None:
        """Thread worker function to play GPIO buzzer tone sequences."""
        if not self._buzzer_initialized or not self._buzzer:
            return

        tones_map = {
            SoundType.MENU_MOVE: [(440, 0.04)],
            SoundType.MENU_SELECT: [(523, 0.04), (659, 0.04), (784, 0.08)],
            SoundType.ERROR: [(150, 0.06), (120, 0.08)],
            SoundType.SNAKE_EAT: [(400, 0.04), (800, 0.04)],
            SoundType.SNAKE_TURN: [(600, 0.02)],
            SoundType.GAME_OVER: [(400, 0.08), (300, 0.08), (200, 0.15)],
            SoundType.HIGH_SCORE: [(523, 0.06), (659, 0.06), (784, 0.06), (1046, 0.18)],
            SoundType.STARTUP_JINGLE: [(440, 0.06), (554, 0.06), (659, 0.06), (880, 0.18)],
            SoundType.PADDLE_HIT: [(480, 0.03)],
            SoundType.WALL_BOUNCE: [(320, 0.03)],
            SoundType.POINT_SCORED: [(523, 0.05), (784, 0.08)],
            SoundType.MATCH_START: [(440, 0.05), (660, 0.08)],
            SoundType.PAUSE: [(350, 0.04), (250, 0.04)],
            SoundType.VICTORY: [(523, 0.08), (659, 0.08), (784, 0.08), (1046, 0.20)],
            SoundType.DEFEAT: [(300, 0.10), (220, 0.10), (150, 0.20)],
        }

        seq = tones_map.get(sound_type, [(440, 0.05)])
        try:
            for freq, dur in seq:
                if self._muted or not self._enabled:
                    break
                if self._is_tonal and Tone:
                    self._buzzer.play(Tone(freq))
                    time.sleep(dur)
                    self._buzzer.stop()
                else:
                    self._buzzer.on()
                    time.sleep(dur)
                    self._buzzer.off()
        except Exception as e:
            logger.error(f"Buzzer playback error: {e}")

    def play_menu_move(self) -> None:
        self.play(SoundType.MENU_MOVE)

    def play_menu_select(self) -> None:
        self.play(SoundType.MENU_SELECT)

    def play_error(self) -> None:
        self.play(SoundType.ERROR)

    def play_snake_eat(self) -> None:
        self.play(SoundType.SNAKE_EAT)

    def play_snake_turn(self) -> None:
        self.play(SoundType.SNAKE_TURN)

    def play_game_over(self) -> None:
        self.play(SoundType.GAME_OVER)

    def play_high_score(self) -> None:
        self.play(SoundType.HIGH_SCORE)

    def play_startup_jingle(self) -> None:
        self.play(SoundType.STARTUP_JINGLE)

    def play_paddle_hit(self) -> None:
        self.play(SoundType.PADDLE_HIT)

    def play_wall_bounce(self) -> None:
        self.play(SoundType.WALL_BOUNCE)

    def play_point_scored(self) -> None:
        self.play(SoundType.POINT_SCORED)

    def play_match_start(self) -> None:
        self.play(SoundType.MATCH_START)

    def play_pause(self) -> None:
        self.play(SoundType.PAUSE)

    def play_victory(self) -> None:
        self.play(SoundType.VICTORY)

    def play_defeat(self) -> None:
        self.play(SoundType.DEFEAT)

    def cleanup(self) -> None:
        """Safely stops active audio and releases mixer/buzzer resources."""
        self.stop_all()
        if self._buzzer_initialized and self._buzzer:
            try:
                self._buzzer.close()
            except Exception as e:
                logger.debug(f"Error closing buzzer hardware: {e}")
        self._enabled = False
        logger.info("AudioManager resources cleaned up.")
