#!/bin/bash

# LOG_FILE="$HOME/speech_to_text_debug.log"
# echo "----------------------------------------" > "$LOG_FILE"
# date >> "$LOG_FILE"
# whoami >> "$LOG_FILE"
# pwd >> "$LOG_FILE"
# env >> "$LOG_FILE"
# echo "----------------------------------------" >> "$LOG_FILE"

export GROQ_API_KEY=YOURKEYHERE

# SPEECH_OUTPUT_FILE="$HOME/speech_output.txt"
# SPEECH_ERROR_FILE="$HOME/speech_error.txt"

python stt.py "$@"
# >  "$SPEECH_OUTPUT_FILE" 2> "$SPEECH_ERROR_FILE"
