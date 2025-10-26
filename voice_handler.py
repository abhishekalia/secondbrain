"""
Voice Handler for Second Brain
Handles text-to-speech output
"""

import pyttsx3
import threading

class VoiceHandler:
    def __init__(self):
        self.engine = None
        self.initialize_engine()
    
    def initialize_engine(self):
        """Initialize text-to-speech engine"""
        try:
            self.engine = pyttsx3.init()
            
            # Configure voice properties
            self.engine.setProperty('rate', 175)  # Speed (words per minute)
            self.engine.setProperty('volume', 0.9)  # Volume (0-1)
            
            # Try to set a good voice
            voices = self.engine.getProperty('voices')
            # Prefer male voice if available
            for voice in voices:
                if 'male' in voice.name.lower() and 'female' not in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
        except Exception as e:
            print(f"TTS initialization error: {e}")
            self.engine = None
    
    def speak(self, text, blocking=True):
        """Convert text to speech using macOS say command"""
        import subprocess
        print(f"[TTS] Speaking: {text}")
        
        try:
            # Use macOS built-in say command (more reliable)
            subprocess.run(['say', text], check=True)
            print(f"[TTS] Done")
            return True
        except Exception as e:
            print(f"[TTS] Error: {e}")
            return False
        
        try:
            # Reinitialize engine each time (pyttsx3 can get stuck)
            self.initialize_engine()
            
            print(f"[TTS] Speaking now...")
            self.engine.say(text)
            self.engine.runAndWait()
            print(f"[TTS] Done speaking")
            return True
        except Exception as e:
            print(f"[TTS] Error: {e}")
            return False
    
    def _speak_thread(self, text):
        """Thread function for non-blocking speech (not used anymore)"""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"TTS thread error: {e}")

# Global voice handler instance
_voice_handler = None

def get_voice_handler():
    """Get or create voice handler singleton"""
    global _voice_handler
    if _voice_handler is None:
        _voice_handler = VoiceHandler()
    return _voice_handler


def speak(text, blocking=False):
    """Convenience function to speak text"""
    handler = get_voice_handler()
    return handler.speak(text, blocking)