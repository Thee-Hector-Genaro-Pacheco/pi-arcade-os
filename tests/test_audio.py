"""
Unit tests for AudioManager in Pi Arcade OS.

Tests volume clamping, muting state transitions, play routing for all SoundType entries,
desktop mixer synthesis, and fallbacks. Runs headlessly.
Works with both unittest and pytest.
"""

import os
# Configure headless environment for Pygame before importing Pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import unittest
import pygame

pygame.init()

from src.config import SoundType
from src.hardware.audio import AudioManager


class TestAudioManager(unittest.TestCase):
    """Unit test suite for AudioManager."""

    def test_volume_clamping_and_setting(self):
        """Test setting volume level and clamping between 0.0 and 1.0."""
        audio = AudioManager(enable_audio=True, volume=0.5)
        self.assertAlmostEqual(audio.volume, 0.5)

        audio.set_volume(0.8)
        self.assertAlmostEqual(audio.volume, 0.8)

        # Clamping upper bound
        audio.set_volume(1.5)
        self.assertAlmostEqual(audio.volume, 1.0)

        # Clamping lower bound
        audio.set_volume(-0.5)
        self.assertAlmostEqual(audio.volume, 0.0)

    def test_mute_unmute_state(self):
        """Test mute(), unmute(), and is_muted() transitions."""
        audio = AudioManager(enable_audio=True, volume=0.7)
        self.assertFalse(audio.is_muted())
        self.assertAlmostEqual(audio.volume, 0.7)

        audio.mute()
        self.assertTrue(audio.is_muted())
        self.assertAlmostEqual(audio._get_effective_volume(), 0.0)

        audio.unmute()
        self.assertFalse(audio.is_muted())
        self.assertAlmostEqual(audio._get_effective_volume(), 0.7)

    def test_play_routing_all_sound_types(self):
        """Test play() routing for every SoundType entry without raising exceptions."""
        audio = AudioManager(enable_audio=True, volume=0.5)

        for sound_type in SoundType:
            audio.play(sound_type)

        # Test specific audio helper methods
        audio.play_menu_move()
        audio.play_menu_select()
        audio.play_error()
        audio.play_snake_eat()
        audio.play_snake_turn()
        audio.play_game_over()
        audio.play_high_score()
        audio.play_startup_jingle()

        audio.stop_all()

    def test_disabled_audio_fallback(self):
        """Test graceful fallback when audio is disabled."""
        audio = AudioManager(enable_audio=False)
        self.assertFalse(audio.is_audio_enabled)

        # Triggering sounds when disabled must never crash
        audio.play(SoundType.MENU_MOVE)
        audio.play_startup_jingle()
        audio.cleanup()

    def test_gpio_buzzer_fallback(self):
        """Test buzzer fallback logic on non-Pi platforms."""
        audio = AudioManager(enable_audio=True)
        # Verify that buzzer worker thread triggers cleanly without throwing errors
        audio._play_buzzer_sequence(SoundType.MENU_MOVE)


if __name__ == "__main__":
    unittest.main()
