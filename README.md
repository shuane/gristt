# gristt Speech-to-Text Dictation for Raspberry Pi

A speech-to-text dictation tool that has been tested on Raspberry Pi (a Debian-based system), using the Groq API for fast Whisper transcription and automatically typing the results into your current application. This _might_ work on other systems that have portaudio installed.

## Features

- **Silence detection**: Automatically stops recording after a period of silence
- **Audio device selection**: Works with any input device (microphone)
- **Debug mode**: Includes audio level visualization and test recordings
- **Keyboard emulation**: Types the transcribed text directly into your active window
- **Lightweight**: Designed to run efficiently on Raspberry Pi hardware

## Disclaimer/issues

Depending on many factors - network, microphone, your accent and so on, this may be too slow for practical use.

## Installation

First, install the required system dependencies:

```bash
# Audio and Python dependencies
sudo apt update
sudo apt install -y python3-pip python3-dev libportaudio2 libasound2-dev python3-pyaudio

# Optional: If you get "default sample format not available" errors
sudo apt install -y libatlas-base-dev
```

Then install the Python packages:

```bash
pip install sounddevice numpy groq pyautogui
```

## Configuration

1. Get your Groq API key from [console.groq.com](https://console.groq.com/)
2. Edit `gristt.sh` and replace `YOURKEYHERE` with your actual API key
3. Make the script executable:
   ```bash
   chmod +x gristt.sh
   ```

## Usage

### Basic dictation

```bash
./gristt.sh
```
Speak into your microphone - it will automatically detect when you stop speaking and type the transcribed text.

On Raspberry Pi you can bind keys (e.g Shift-Alt-D) using the Keyboard settings applet, put the full path to gristt.sh and any parameters you need.

### Advanced options

```bash
# List available audio devices
./gristt.sh --list-devices

# Use specific audio device (use ID from --list-devices)
./gristt.sh --device 2

# Test audio input levels without typing
./gristt.sh --test

# Adjust silence detection (default: 0.004 threshold, 3.0s timeout)
./gristt.sh --threshold 0.005 --timeout 2.5

# Enable debug mode for troubleshooting
./gristt.sh --debug
```

## Troubleshooting

If you encounter issues:

1. **No audio detected**:
   - Run with `--test` to check input levels
   - Try different `--threshold` values (start with 0.01)
   - Verify microphone permissions and volume

2. **Audio quality problems**:
   - Use `--debug` to save test recordings
   - Try a USB microphone if a bluetooth mic has issues

3. **Performance**:
   - On older Pis, you might need to increase `--timeout` to 4-5 seconds
   - Reduce background processes while dictating

## How it works

The system combines several components:

1. `sounddevice` captures audio from the microphone with efficient numpy buffers
2. Custom silence detection stops recording when you finish speaking
3. Audio is sent to Groq's Whisper API for fast, accurate transcription
4. `pyautogui` types the results into your active window

The entire pipeline is optimized for Raspberry Pi's limited resources while maintaining good transcription accuracy.

## License

Apache2

