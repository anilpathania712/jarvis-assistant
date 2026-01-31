
# Jarvis Assistant – Open-Source Voice-Controlled AI Assistant

Jarvis Assistant is an open-source, voice-controlled AI personal assistant. It listens to your voice commands, responds naturally, and performs real system actions like opening apps, controlling media, searching the web, and managing system settings.

The backend is powered by Python (Flask + Faster-Whisper) for audio processing, AI intent analysis, and task automation. The frontend is built using React + Tailwind CSS to provide a modern interface with audio playback support.


## Features

- Voice-Only Interaction – Fully controlled via speech; no typing required

- Conversational AI – Understands queries and responds naturally

- Website & Application Launching – Open URLs or local apps via voice commands

- System Automation – Lock screen, adjust volume, wake display, shutdown/restart system

- Media & Text Automation – Control music, type text, search Google, fetch Wikipedia summaries, tell jokes

- Optimized Speech Recognition – Uses Faster-Whisper (CPU, INT8) for fast and efficient transcription

- Text-to-Speech Responses – AI replies with natural voice feedback

- Open-Source & Local Execution – Runs locally with free AI models; no paid APIs required

- Modular & Extensible – Easily add new commands or tools
## Tech Stack

- Frontend: React, Tailwind CSS

- Backend: Python, Flask

- AI Models: Faster-Whisper (CPU, INT8) – Fast and lightweight Speech-to-Text

- Groq API (Llama models) – Intent recognition & AI conversation
  
- Other Libraries:pyttsx3 – Text-to-Speech

pyautogui – Automation

wikipedia – Knowledge lookup

pyjokes – Joke generation

webbrowser – Open websites

ffmpeg – Audio conversion

python-dotenv – Environment variables

CTranslate2 – Backend engine for Faster-Whisper

- OS Support: Windows, macOS, Linux
