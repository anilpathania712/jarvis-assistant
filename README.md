
# Jarvis Assistant – Open-Source Voice-Controlled AI Assistant

Jarvis Assistant is an open-source, voice-controlled AI personal assistant. It can listen to your voice commands, respond naturally, and perform actions like:

- Opening websites

- Launching desktop applications

- Controlling media and volume

- Providing Wikipedia summaries, jokes, or Google search results

- Locking, shutting down, or restarting your system

The backend is powered by Python (Flask, Whisper, PyTorch) for audio processing, AI intent analysis, and task automation. The frontend is built with React + Tailwind CSS to provide a modern interface with audio playback support.




## Features

- Voice-Only Interaction: Fully controlled via speech; no typing required.

- Conversational AI: Understands queries and responds naturally.

- Website & Application Launching: Open URLs or local apps via voice commands.

- System Automation: Lock screen, adjust volume, wake display, shutdown/restart system.

- Media & Text Automation: Control music, type text, search Google, fetch Wikipedia summaries, tell jokes.

- Open-Source & Local Execution: Runs entirely locally with free AI models; no paid APIs required.

- Modular & Extensible: Easily add new commands or tools.
## Tech Stack

- Frontend: React, Tailwind CSS

- Backend: Python, Flask

- AI Models: Whisper (Speech-to-Text), Free AI models via Groq API for intent analysis

- Other Libraries: pyttsx3 (Text-to-Speech), pyautogui (Automation), wikipedia, pyjokes, webbrowser, ffmpeg

- OS Support: Windows, macOS, Linux