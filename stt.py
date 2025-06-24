import os
import sounddevice as sd
import numpy as np
import threading
import time
import wave
import groq
from io import BytesIO
import argparse
import pyautogui  # For keyboard emulation

groq_client = groq.Client()

def list_audio_devices():
    """List all available audio input devices"""
    devices = sd.query_devices()
    print("\nAVAILABLE AUDIO INPUT DEVICES:")
    print("-" * 50)
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:  # Only show input devices
            default = " (DEFAULT)" if device['name'] == sd.query_devices(kind='input')['name'] else ""
            print(f"{i}: {device['name']}{default} - {device['max_input_channels']} channels")
    print("-" * 50)
    return devices

class SpeechRecognizer:
    def __init__(self, silence_threshold=0.004, silence_timeout=3.0, sample_rate=16000, device=None, debug=False):
        self.silence_threshold = silence_threshold
        self.silence_timeout = silence_timeout
        self.sample_rate = sample_rate
        self.recording = False
        self.audio_data = []
        self.device = device  # Can be None (default), or device index
        self.debug = debug
        
    def test_audio_input(self, duration=5):
        """Test the selected audio input by recording for a few seconds and displaying levels"""
        if not self.debug:
            return True
            
        print(f"\nTesting audio input device for {duration} seconds...")
        print("Speak into your microphone to see if levels respond")
        print("You should see the numbers rise when you speak\n")
        
        audio_data = []
        levels = []
        
        def callback(indata, frames, time_info, status):
            if status:
                print(f"Error: {status}")
            volume_norm = np.linalg.norm(indata) / frames
            levels.append(volume_norm)
            audio_data.append(indata.copy())
            bars = int(volume_norm * 50)
            print(f"Level: {volume_norm:.4f} {'|' * bars}", end="\r")
            
        try:
            with sd.InputStream(callback=callback, channels=1, samplerate=self.sample_rate, device=self.device):
                time.sleep(duration)
        except Exception as e:
            print(f"\nError testing audio input: {e}")
            return False
            
        max_level = max(levels) if levels else 0
        avg_level = sum(levels) / len(levels) if levels else 0
        
        print("\n\nAudio Input Test Results:")
        print(f"Maximum level detected: {max_level:.4f}")
        print(f"Average level detected: {avg_level:.4f}")
        
        if max_level < 0.004:
            print("\nWARNING: Very low audio levels detected!")
            print("Possible issues:")
            print("1. Microphone may be muted")
            print("2. Wrong input device selected")
            print("3. Microphone permissions issue")
            return False
        else:
            print("\nAudio input appears to be working")
            if max_level < 0.05:
                print("Note: Audio levels are a bit low, you may want to increase microphone volume")
            
            # Save the test audio
            if audio_data and self.debug:
                combined = np.concatenate(audio_data, axis=0)
                self.save_debug_audio(combined, "audio_test.wav")
                print("Test audio saved to 'audio_test.wav'")
            
            return True
        
    def record_with_silence_detection(self):
        self.recording = True
        self.audio_data = []
        last_sound_time = time.time()
        peak_volume = 0
        
        def audio_callback(indata, frames, time_info, status):
            if status and self.debug:
                print(f"Status: {status}")
                
            nonlocal last_sound_time, peak_volume
            volume_norm = np.linalg.norm(indata) / frames
            peak_volume = max(peak_volume, volume_norm)
            
            # Visual volume indicator (only in debug mode)
            if self.debug:
                bars = int(volume_norm * 50)
                print(f"Level: {volume_norm:.4f} {'|' * bars}", end="\r")
            
            if self.recording:
                self.audio_data.append(indata.copy())
                
                # If sound detected, update the last sound time
                if volume_norm > self.silence_threshold:
                    last_sound_time = time.time()
                # If silent for too long, stop recording
                elif (time.time() - last_sound_time > self.silence_timeout):
                    self.recording = False
        
        if self.debug:
            print("Listening... (speak or press Ctrl+C to stop)")
        else:
            print("Listening...")
            
        try:
            with sd.InputStream(callback=audio_callback, channels=1, samplerate=self.sample_rate, device=self.device):
                while self.recording:
                    time.sleep(0.1)
        except Exception as e:
            if self.debug:
                print(f"\nError recording audio: {e}")
            return None
        
        if self.debug:
            print(f"\nRecording finished. Peak volume: {peak_volume:.4f}")
            
            if peak_volume < 0.004:
                print("WARNING: Very little audio was detected. Check your microphone.")
            
        if self.audio_data:
            audio = np.concatenate(self.audio_data, axis=0)
            if self.debug:
                max_amplitude = np.max(np.abs(audio))
                print(f"Max audio amplitude: {max_amplitude:.4f}")
            return audio
        else:
            return None
    
    def transcribe_with_groq(self, audio_data):
        """Transcribe audio using Groq's Whisper API with better error reporting"""
        # Save audio to in-memory file
        wav_bytes = BytesIO()
        with wave.open(wav_bytes, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
        
        wav_bytes.seek(0)
        
        try:
            # Add debugging info
            if self.debug:
                print("Sending audio to Groq API...")
                print(f"Audio length: {len(audio_data)/self.sample_rate:.2f} seconds")
            else:
                print("Transcribing...")
            
            # Call Groq API with Whisper model
            response = groq_client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=("audio.wav", wav_bytes)
            )
            return response.text
        except Exception as e:
            if self.debug:
                print(f"Detailed error with Groq API: {str(e)}")
                # Print full traceback for debugging
                import traceback
                traceback.print_exc()
            else:
                print(f"Transcription error: {e}")
            return None
    
    def save_debug_audio(self, audio_data, filename="debug_audio.wav"):
        """Save the recorded audio to a file for debugging"""
        if audio_data is not None and self.debug:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            print(f"Saved debug audio to {filename}")


def type_text(text):
    """Type the transcribed text using pyautogui"""
    if not text:
        return
        
    # Add a small delay before typing
    time.sleep(0.3)
    
    # Type the text
    pyautogui.write(text)


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Speech-to-text dictation tool')
    parser.add_argument('--device', type=int, help='Audio input device ID')
    parser.add_argument('--list-devices', action='store_true', help='List available audio input devices')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with verbose output')
    parser.add_argument('--test', action='store_true', help='Test audio input without typing')
    parser.add_argument('--threshold', type=float, default=0.004, help='Silence threshold (default: 0.004)')
    parser.add_argument('--timeout', type=float, default=3.0, help='Silence timeout in seconds (default: 3.0)')
    args = parser.parse_args()
    
    # If only listing devices is requested
    if args.list_devices:
        list_audio_devices()
        return
    
    # Create recognizer with selected device
    recognizer = SpeechRecognizer(
        silence_threshold=args.threshold,
        silence_timeout=args.timeout,
        device=args.device,
        debug=args.debug
    )
    
    # Test audio input if requested
    if args.test or args.debug:
        if not recognizer.test_audio_input(duration=5):
            print("\nAudio input test failed or showed very low levels.")
            retry = input("Continue anyway? (y/n): ")
            if retry.lower() != 'y':
                print("Exiting. Please check your microphone settings.")
                return
    
    try:
        print("Ready to record. Speak now...")
        audio_data = recognizer.record_with_silence_detection()
        if audio_data is not None and len(audio_data) > 0:
            # Save audio for debugging
            if args.debug:
                recognizer.save_debug_audio(audio_data)
            
            text = recognizer.transcribe_with_groq(audio_data)
            if text:
                if args.debug:
                    print(f"Transcription: {text}")
                else:
                    print(f"Typing: {text}")
                
                if not args.test:
                    type_text(text)
            else:
                print("Transcription failed")
        else:
            print("No audio recorded")
    except KeyboardInterrupt:
        print("\nStopped by user")
        recognizer.recording = False


if __name__ == "__main__":
    main()

