from flask import Flask, request, jsonify, send_file        # Flask framework and utilities for web app and API handling
from flask_cors import CORS                                # Enable Cross-Origin Resource Sharing (CORS) for API access from other domains
from faster_whisper import WhisperModel                     # OpenAI Whisper model for speech-to-text transcription
import tempfile                                             # Create and manage temporary files (e.g., uploaded audio)
import os                                                   # Interact with the operating system (file paths, environment variables)
import datetime                                             # Handle dates and times for logging, timestamps, file naming
import wikipedia                                           # Fetch summaries or pages from Wikipedia
import pyjokes                                              # Generate random jokes (programming/general)
import webbrowser                                           # Open URLs in the default web browser
import platform                                             # Get system/platform information (OS, version, architecture)
import subprocess                                          # Run external commands or programs
import pyautogui                                            # Automate keyboard/mouse actions and take screenshots
import json                                                 # Parse and generate JSON data
import inspect                                              # Introspection for examining functions, classes, objects
import pyttsx3                                              # Text-to-speech library for making the assistant speak
from openai import OpenAI                                   # Access OpenAI APIs for GPT models, embeddings, etc.
from dotenv import load_dotenv

# --- CONFIGURATION ---

# Initialize the Flask web application
app = Flask(__name__)

# Enable CORS (Cross-Origin Resource Sharing) to allow the frontend 
# (which might be on a different port/domain) to communicate with this backend.
CORS(app, resources={r"/*": {"origins": "*"}})

print("Loading Faster-Whisper model (CPU, INT8)...")
# 2. Load the Whisper "base" model onto the CPU.
model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"   # very fast on CPU
)
print("Faster-Whisper loaded successfully.")

load_dotenv()  # loads .env into environment

# --- SETUP GROQ CLIENT ---
# Initialize the OpenAI client but point it to Groq's API endpoint.
# Groq provides very fast inference for open-source models like Llama 3.
# Note: API keys should ideally be stored in environment variables for security.

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("API_KEY"))

# Identify the Operating System to execute platform-specific commands later
OS_NAME = platform.system()


# --- 1. SYSTEM FUNCTIONS (Tools the AI can use) ---

def open_application(app_name):
    """
    Opens a local application. Includes a mapping for common apps to ensure accuracy.
    """
    try:
        app_name = app_name.lower()
        
        # Dictionary mapping voice keywords (e.g., "vscode") to actual system executable names (e.g., "code")
        app_mapping = {
            "chrome": "chrome",
            "google chrome": "chrome",
            "spotify": "spotify",
            "notepad": "notepad",
            "calculator": "calc",
            "calc": "calc",
            "vscode": "code",
            "visual studio code": "code",
            "excel": "excel",
            "word": "winword",
            "powerpoint": "powerpnt",
            "edge": "msedge",
            "firefox": "firefox"
        }
        
        # Look up the executable name, defaulting to the input if not found
        target_app = app_mapping.get(app_name, app_name)
        
        # Execute the command based on the detected OS
        if OS_NAME == "Windows":
            # 'start' is the Windows command to launch a program
            os.system(f"start {target_app}")
        elif OS_NAME == "Darwin":  # macOS
            # 'open -a' is the macOS command to launch an application by name
            os.system(f"open -a {target_app}")
        elif OS_NAME == "Linux":
            # On Linux, we call the executable directly (assuming it's in the PATH)
            subprocess.call([target_app])
            
        return f"Opened {app_name}."
    except Exception as e:
        return f"Failed to open {app_name}. Error: {str(e)}"

def lock_screen():
    """Locks the workstation."""
    try:
        if OS_NAME == "Windows":
            # Windows DLL call to lock the workstation
            os.system("rundll32.exe user32.dll,LockWorkStation")
        elif OS_NAME == "Darwin":
            # AppleScript to trigger the lock screen shortcut (Cmd+Ctrl+Q)
            os.system('osascript -e \'tell application "System Events" to keystroke "q" using {command down, control down}\'')
        return "Locking screen."
    except Exception as e:
        return f"Error locking screen: {str(e)}"

def system_volume(action):
    """
    Controls system volume robustly across OS.
    Actions: 'up', 'down', 'mute'
    """
    try:
        if OS_NAME == "Windows":
            # Map actions to Windows multimedia key codes
            key_map = {"up": "175", "down": "174", "mute": "173"}
            key_code = key_map.get(action)
            if key_code:
                # Use PowerShell to simulate a key press (Volume Up/Down/Mute)
                os.system(f"powershell -c \"(New-Object -ComObject WScript.Shell).SendKeys([char]{key_code})\"")
                
        elif OS_NAME == "Darwin":  # macOS
            # Use osascript to set the volume output property
            if action == "up":
                os.system('osascript -e "set volume output volume (output volume + 10)"')
            elif action == "down":
                os.system('osascript -e "set volume output volume (output volume - 10)"')
            elif action == "mute":
                os.system('osascript -e "set volume output volume 0"')
                
        elif OS_NAME == "Linux":
            # Use 'amixer' command-line tool for audio on Linux
            if action == "up":
                subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "5%+"])
            elif action == "down":
                subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "5%-"])
            elif action == "mute":
                subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "toggle"])
                
        return f"Volume {action}."
    except Exception as e:
        return f"Error changing volume: {str(e)}"

def shutdown_system():
    """Shuts down the computer."""
    try:
        if OS_NAME == "Windows":
            os.system("shutdown /s /t 1")
        elif OS_NAME == "Darwin":
            os.system("shutdown -h now")
        elif OS_NAME == "Linux":
            os.system("shutdown now")
        return "Shutting down system now."
    except Exception as e:
        return f"Could not shutdown. Error: {str(e)}"

def restart_system():
    """Restarts the computer."""
    try:
        if OS_NAME == "Windows":
            os.system("shutdown /r /t 1")
        elif OS_NAME == "Darwin":
            os.system("shutdown -r now")
        elif OS_NAME == "Linux":
            os.system("reboot")
        return "Restarting system now."
    except Exception as e:
        return f"Could not restart. Error: {str(e)}"

def wake_screen():
    """Wakes the screen up (Simulates mouse movement)."""
    try:
        # Move the mouse slightly to trigger display wake-up
        pyautogui.moveRel(10, 10)
        pyautogui.moveRel(-10, -10)
        return "Waking screen."
    except Exception as e:
        return f"Could not wake screen: {str(e)}"

def generate_tts(text):
    """Generates a .wav audio file from text using pyttsx3."""
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        # Try to find a decent voice (David/Zira on Windows, Google on other platforms)
        for voice in voices:
            if "david" in voice.name.lower() or "zira" in voice.name.lower() or "google" in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        
        # Create a temporary file to save the audio
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = temp_file.name
        temp_file.close() 

        # Save the spoken text to the file and run the engine
        engine.save_to_file(text, temp_path)
        engine.runAndWait()
        return temp_path
    except Exception as e:
        print(f"TTS Error: {e}")
        return None


# --- 2. DYNAMIC TOOL REGISTRY ---
# This dictionary maps string names (defined in the AI schema below) to the actual python functions above.
# When the AI returns a function name (e.g., "open_application"), Python looks it up here to execute it.
TOOL_REGISTRY = {
    "open_website": webbrowser.open,
    "open_application": open_application,
    "media_control": pyautogui.press,
    "volume_control": system_volume,
    "search_google": lambda q: webbrowser.open(f"https://www.google.com/search?q={q}"),
    "get_wikipedia": lambda q: wikipedia.summary(q, sentences=2),
    "get_time": lambda **kwargs: datetime.datetime.now().strftime("%I:%M %p"),
    "get_date": lambda **kwargs: datetime.datetime.now().strftime("%B %d, %Y"),
    "tell_joke": lambda **kwargs: pyjokes.get_joke(),
    "type_text": pyautogui.typewrite,
    "lock_screen": lock_screen,
    "shutdown_system": shutdown_system,
    "restart_system": restart_system,
    "wake_screen": wake_screen,
}


# --- 3. THE BRAIN (AI PROCESSOR) ---

def analyze_intent_with_ai(user_text):
    """Sends the user text to AI to determine intent and parameters."""
    
    # Define the "Tools" (Function Calling schema) available to the LLM.
    # This tells the AI what functions exist, what they do, and what arguments they require.
    tools_definition = [
        {"type": "function", "function": {
            "name": "open_website", 
            "description": "Opens a specific website URL. Use for requests like 'open YouTube', 'open ChatGPT', 'open Netflix'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The full URL (e.g., https://youtube.com)"}
                },
                "required": ["url"]
            }
        }},
        {"type": "function", "function": {
            "name": "open_application", 
            "description": "Opens a local installed application. Use for 'open spotify', 'open notepad', 'open calculator'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the app (e.g., spotify, notepad, calc)"}
                },
                "required": ["app_name"]
            }
        }},
        {"type": "function", "function": {
            "name": "media_control", 
            "description": "Controls music playback. Supports 'nexttrack', 'prevtrack', 'playpause'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["nexttrack", "prevtrack", "playpause"]}
                },
                "required": ["action"]
            }
        }},
        {"type": "function", "function": {
            "name": "volume_control", 
            "description": "Changes system volume. Supports 'up' (increase), 'down' (decrease), 'mute'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["up", "down", "mute"], "description": "The volume action to perform"}
                },
                "required": ["action"]
            }
        }},
        {"type": "function", "function": {
            "name": "search_google", 
            "description": "Searches Google for a term.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search term"}
                },
                "required": ["query"]
            }
        }},
        {"type": "function", "function": {
            "name": "get_wikipedia", 
            "description": "Looks up a topic on Wikipedia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "The topic to search"} 
                },
                "required": ["q"]
            }
        }},
        {"type": "function", "function": {
            "name": "type_text", 
            "description": "Types text into the currently focused window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"}
                },
                "required": ["text"]
            }
        }},
        {"type": "function", "function": {
            "name": "get_time", 
            "description": "Gets current time.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }},
        {"type": "function", "function": {
            "name": "get_date", 
            "description": "Gets current date.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }},
         {"type": "function", "function": {
            "name": "lock_screen", 
            "description": "Locks the computer screen.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }},
        {"type": "function", "function": {
            "name": "shutdown_system", 
            "description": "Shuts down the computer completely.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }},
        {"type": "function", "function": {
            "name": "restart_system", 
            "description": "Restarts or reboots the computer.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }},
        {"type": "function", "function": {
            "name": "wake_screen", 
            "description": "Wakes the computer screen up if it is asleep (switches on display).",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }},
        {"type": "function", "function": {
            "name": "tell_joke", 
            "description": "Tells a random joke.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }}
    ]

    try:
        model_name = "llama-3.1-8b-instant" 
        
        # JARVIS Persona: Efficient, formal, authoritative.
        messages = [
            {
                "role": "system", 
                "content": (
                    "You are JARVIS, a highly advanced AI assistant. "
                    "You are efficient, slightly formal, and execute commands immediately. "
                    "When the user asks for a task, use the appropriate tool. "
                    "After performing an action, provide a short, crisp confirmation (e.g., 'Done.' or 'Opened YouTube'). "
                    "Do not ask unnecessary questions. If you perform an action, acknowledge it."
                )
            },
            {"role": "user", "content": user_text}
        ]

        print(f"[LOG] Analyzing intent for: '{user_text}'")

        # Call the Groq API with the tools definition
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools_definition,
            tool_choice="auto"  # Let the model decide whether to call a function or just chat
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # Check if AI decided to use a tool (Execute a command)
        if tool_calls:
            print(f"[LOG] Command identified. Executing system order...")
            
            # 1. Append the function call request to history so the AI knows context for next steps
            messages.append(response_message)

            # 2. Execute the functions locally
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = TOOL_REGISTRY.get(function_name)
                
                if function_to_call:
                    # Parse arguments provided by the AI (e.g., {"app_name": "spotify"})
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Filter arguments to match function signature (prevents errors if extra args sent)
                    sig = inspect.signature(function_to_call)
                    filtered_args = {k: v for k, v in function_args.items() if k in sig.parameters}
                    
                    # Execute the actual Python function
                    try:
                        print(f"[LOG] Running {function_name} with args {filtered_args}")
                        function_response = function_to_call(**filtered_args)
                    except Exception as e:
                        function_response = f"Error: {str(e)}"
                        print(f"[LOG] Execution failed: {e}")
                else:
                    function_response = "Error: Function not found."

                # 3. Append the result of the function execution back to conversation
                # This allows the AI to formulate a final sentence based on the result (e.g., "Spotify is now open")
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(function_response),
                    }
                )
            
            # 4. Get final verbal response based on the result
            print("[LOG] Formulating verbal response...")
            second_response = client.chat.completions.create(
                model=model_name,
                messages=messages,
            )
            
            return {
                "type": "action_success", 
                "content": second_response.choices[0].message.content
            }

        else:
            # It's a general chat question (No tools used)
            print("[LOG] General chat query detected.")
            return {
                "type": "chat",
                "content": response_message.content
            }

    except Exception as e:
        print(f"AI Error: {e}")
        return {"type": "error", "content": "I encountered a problem processing that request."}


# --- FLASK ROUTES ---

@app.route("/voice", methods=["POST"])
def voice_command():
    """
    Main endpoint: Receives audio, transcribes it, processes intent, and returns text + audio file.
    """
    try:
        # Check if an audio file was uploaded in the request
        if "audio" not in request.files:
            return jsonify({"error": "No audio file received"}), 400

        audio = request.files["audio"]

        # 1. Transcribe Audio (Whisper)
        # Save uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp:
            audio.save(temp.name)
            webm_path = temp.name

        # Prepare path for the converted WAV file (Whisper needs WAV/MP3, not Webm usually)
        wav_path = webm_path.replace(".webm", ".wav")
        
        # Convert Webm to Wav using ffmpeg (FFmpeg must be installed on the system)
        exit_code = os.system(f'ffmpeg -y -i "{webm_path}" "{wav_path}"')
        
        if exit_code != 0:
            return jsonify({"error": "FFmpeg conversion failed. Ensure FFmpeg is installed."}), 500

        print("[LOG] Transcribing audio...")
        segments, info = model.transcribe(wav_path)
        text = " ".join(segment.text for segment in segments).strip()

        # Cleanup audio files (Delete temp files)
        os.remove(webm_path)
        os.remove(wav_path)

        if not text:
            return jsonify({"heard": "", "response": "I heard nothing."})

        # 2. Analyze Intent & Execute (AI)
        intent = analyze_intent_with_ai(text)

        # 3. Get Response Text
        response_text = intent.get("content", "I didn't understand that.")

        # 4. Generate TTS Audio
        audio_path = generate_tts(response_text)
        
        # Extract just the filename (not full path) for sending to client
        filename = os.path.basename(audio_path) if audio_path else None

        return jsonify({
            "heard": text,
            "response": response_text,
            "audio_filename": filename 
        })

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/tts/<filename>", methods=["GET"])
def get_tts_file(filename):
    """
    Serves the generated audio file back to the frontend.
    The frontend receives the filename from /voice, then calls this endpoint to download/play it.
    """
    try:
        # Locate file in the system's temp directory
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        if os.path.exists(file_path):
            return send_file(file_path, mimetype="audio/wav")
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- MAIN ENTRY POINT ---
if __name__ == "__main__":
    print("------------------------------------------------")
    print("JARVIS SYSTEM ONLINE")
    print(f"OS Detected: {OS_NAME}")
    print("Whisper Model: Loaded (FP32 Precision)")
    print("Groq API: Connected")
    print("Waiting for voice commands...")
    print("------------------------------------------------")
    # Run Flask server accessible on the local network
    app.run(host="0.0.0.0", port=5000, debug=True)