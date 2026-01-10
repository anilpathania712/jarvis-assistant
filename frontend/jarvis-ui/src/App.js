import { useState, useRef, useEffect } from "react";

function App() {
  const [recording, setRecording] = useState(false);
  const [heard, setHeard] = useState("");
  const [response, setResponse] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  // Audio & UI Refs
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const silenceTimerRef = useRef(null);
  const animationRef = useRef(null);

  // Initialize Browser Voices
  useEffect(() => {
    const loadVoices = () => {
      window.speechSynthesis.getVoices();
    };
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }, []);

  // Audio Analysis Loop (Visualization & Silence Detection)
  const detectSilence = () => {
    if (!analyserRef.current) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyserRef.current.getByteFrequencyData(dataArray);

    // Calculate Average Volume
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
      sum += dataArray[i];
    }
    const average = sum / bufferLength;

    // Visualizer Logic: Update DOM elements for high performance
    const core = document.getElementById('ai-core');
    const ring = document.getElementById('ai-ring');
    const glow = document.getElementById('ai-glow');
    
    if (recording) {
      animationRef.current = requestAnimationFrame(detectSilence);
      
      // Calculate dynamic scale based on voice volume
      const scaleFactor = 1 + (average / 128) * 0.3; 
      const opacityFactor = 0.3 + (average / 256);
      
      if (core) {
        core.style.transform = `scale(${scaleFactor})`;
        core.style.boxShadow = `0 0 ${average * 0.5}px rgba(0, 243, 255, ${opacityFactor})`;
      }
      if (ring) {
        ring.style.transform = `scale(${scaleFactor * 1.1})`;
        ring.style.opacity = opacityFactor;
        ring.style.borderColor = `rgba(0, 243, 255, ${opacityFactor})`;
      }
      if (glow) {
        glow.style.opacity = opacityFactor * 0.5;
      }
    }

    // Silence Detection Logic
    if (recording) {
      if (average < 15) { // Threshold for silence
        if (!silenceTimerRef.current) {
          silenceTimerRef.current = setTimeout(() => {
            stopRecording();
          }, 1500); // Stop after 1.5s of silence
        }
      } else {
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }
      }
    }
  };

  const startRecording = async () => {
    // Reset states
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsProcessing(false);
    setHeard("");
    setResponse("");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);

      mediaRecorderRef.current = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        chunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = handleStop;

      mediaRecorderRef.current.start();
      setRecording(true);
      detectSilence(); // Start visualizer loop

    } catch (err) {
      console.error("Mic Error:", err);
      alert("Microphone access is required to proceed.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
      
      // Cleanup Animation Loop
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;

      // Reset visual elements
      const core = document.getElementById('ai-core');
      if (core) {
        core.style.transform = `scale(1)`;
        core.style.boxShadow = `none`;
      }
      
      // Stop stream tracks
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const handleStop = async () => {
    setIsProcessing(true);
    
    const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("audio", audioBlob);

    try {
      // Pointing to local Flask/Python server
      const res = await fetch("http://127.0.0.1:5000/voice", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Server error");
      
      const data = await res.json();
      setHeard(data.heard);
      setResponse(data.response);

      // Play Server Audio if available, else fallback to browser TTS
      if (data.audio_filename) {
        setIsSpeaking(true);
        const audioUrl = `http://127.0.0.1:5000/tts/${data.audio_filename}`;
        const audio = new Audio(audioUrl);
        audio.play();
        audio.onended = () => setIsSpeaking(false);
      } else {
        speak(data.response);
      }
      
    } catch (error) {
      console.error("Upload error:", error);
      setResponse("System offline or connection refused.");
      speak("Connection failed.");
    } finally {
      setIsProcessing(false);
    }
  };

  const speak = (text) => {
    if (!text) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(voice => 
      voice.name.includes("Google US English") || 
      voice.name.includes("Samantha") || 
      voice.name.includes("Microsoft Aria") ||
      (voice.lang === "en-US" && voice.name.includes("Female"))
    );
    
    if (preferredVoice) utter.voice = preferredVoice;
    utter.pitch = 1.0;
    utter.rate = 1.0;

    utter.onstart = () => setIsSpeaking(true);
    utter.onend = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utter);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioContextRef.current) audioContextRef.current.close();
      window.speechSynthesis.cancel();
    };
  }, []);

return (
  <div className="min-h-screen w-full bg-[#02000a] text-white font-['Orbitron',sans-serif] overflow-hidden relative">
    {/* === Enhanced deep space background === */}
    <div className="absolute inset-0 pointer-events-none">
      {/* Very subtle starfield */}
      <div className="absolute inset-0 bg-[radial-gradient(#ffffff_1px,transparent_1px)] bg-[length:80px_80px] opacity-[0.035] mix-blend-screen"></div>
      <div className="absolute inset-0 bg-[radial-gradient(#a5b4fc_1px,transparent_1px)] bg-[length:140px_140px] opacity-[0.018] animate-slow-twinkle"></div>

      {/* Nebula / atmospheric mood */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-950/40 via-purple-950/20 to-black/70"></div>
      <div className="absolute inset-0 bg-gradient-radial from-cyan-900/16 via-transparent to-transparent opacity-80 at-20%_15%"></div>
      <div className="absolute inset-0 bg-gradient-radial from-violet-900/14 via-transparent to-transparent opacity-70 at-80%_75%"></div>

      {/* Floating energy auras - softer & more cinematic */}
      <div className="absolute -top-1/3 -left-1/4 w-[140vw] h-[140vw] bg-gradient-to-br from-cyan-700/8 to-transparent rounded-full blur-3xl animate-very-slow-drift"></div>
      <div className="absolute -bottom-1/3 -right-1/4 w-[130vw] h-[130vw] bg-gradient-to-tl from-purple-800/9 to-transparent rounded-full blur-[200px] animate-very-slow-drift-delayed"></div>
    </div>

    {/* === Main Content === */}
    <div className="relative z-10 min-h-screen flex items-center justify-center px-5 sm:px-8 md:px-12 lg:px-16 xl:px-24 py-12">
      <div className="w-full max-w-7xl grid grid-cols-1 lg:grid-cols-12 gap-8 xl:gap-16">

        {/* ======================== */}
        {/*        ORB / CORE        */}
        {/* ======================== */}
        <div className="lg:col-span-7 relative flex items-center justify-center order-2 lg:order-1">
          <div className="relative perspective-[1400px]">
            <button
              onClick={recording ? stopRecording : startRecording}
              className={`
                group relative w-72 h-72 sm:w-96 sm:h-96 md:w-[420px] md:h-[420px]
                transition-all duration-1000 ease-out transform-gpu
                ${recording ? 'scale-[1.12] rotate-[2deg]' : 'hover:scale-[1.035] active:scale-95'}
              `}
            >
              {/* Outer resonance rings */}
              <div className={`absolute inset-[-60px] rounded-full border border-cyan-400/25 transition-all duration-1200 ease-out
                ${recording ? 'animate-spin-slow scale-110 border-cyan-300/55 opacity-90' : 'opacity-30 scale-95'}`}
              />
              <div className={`absolute inset-[-100px] rounded-full border border-purple-400/20 transition-all duration-3000 ease-in-out
                ${isSpeaking ? 'animate-spin-reverse scale-110 border-purple-300/45 opacity-70' : 'opacity-20 scale-90'}`}
              />

              {/* Core orb - main attraction */}
              <div className={`
                relative w-full h-full rounded-full 
                flex items-center justify-center overflow-hidden
                border border-white/5 backdrop-blur-2xl shadow-[0_0_120px_rgba(0,0,0,0.85),inset_0_0_60px_rgba(0,0,0,0.6)]
                transition-all duration-800 ease-out
                ${recording ? 'border-cyan-300/80 shadow-cyan-600/50 bg-gradient-to-br from-cyan-950/40 via-black/60 to-cyan-950/30' :
                  isSpeaking ? 'border-purple-300/70 shadow-purple-700/45 bg-gradient-to-br from-purple-950/35 via-black/60 to-purple-950/25 animate-soft-breathe' :
                  isProcessing ? 'border-amber-400/60 shadow-amber-600/40 bg-gradient-to-br from-amber-950/30 via-black/60 to-amber-950/20' :
                  'border-white/8 bg-gradient-to-br from-slate-950/60 via-black/70 to-slate-950/50 hover:border-white/20 hover:shadow-[0_0_100px_rgba(180,200,255,0.18)]'}
              `}>
                {/* Scan line / energy field */}
                <div className={`absolute inset-0 bg-gradient-to-r from-transparent via-white/4 to-transparent 
                  animate-scan-horizontal pointer-events-none
                  ${recording || isSpeaking ? 'opacity-75' : 'opacity-25'}`}
                />

                {/* Center glyph - bigger & sharper */}
                <div className={`
                  relative text-[10rem] sm:text-[12rem] md:text-[14rem] lg:text-[16rem] font-black tracking-[-0.04em]
                  transition-all duration-700 drop-shadow-[0_0_40px_rgba(255,255,255,0.4)]
                  ${recording ? 'text-cyan-200 animate-strong-pulse' :
                    isSpeaking ? 'text-purple-200 animate-breathe-strong' :
                    isProcessing ? 'text-amber-200 animate-spin-slow' :
                    'text-white/70 group-hover:text-white group-hover:scale-105 group-hover:rotate-[4deg]'}
                `}>
                  {recording ? '■' :
                   isSpeaking ? '⚡' :
                   isProcessing ? '⟐' :
                   'J'}
                </div>

                {/* Very subtle inner glow */}
                <div className="absolute inset-[15%] rounded-full bg-gradient-radial from-white/8 via-transparent to-transparent pointer-events-none" />
              </div>
            </button>

            {/* Status text + minimal waveform */}
            <div className="absolute -bottom-20 sm:-bottom-24 left-1/2 -translate-x-1/2 w-full text-center">
              <div className={`
                text-base sm:text-lg md:text-xl font-black tracking-[0.35em] uppercase
                transition-colors duration-700 mb-4 drop-shadow-md
                ${recording ? 'text-cyan-300' :
                  isSpeaking ? 'text-purple-300' :
                  isProcessing ? 'text-amber-300' :
                  'text-white/40'}
              `}>
                {recording ? "AUDIO CAPTURE ACTIVE" :
                 isSpeaking ? "SPEECH SYNTHESIS" :
                 isProcessing ? "NEURAL PROCESSING" :
                 "STANDBY MODE"}
              </div>

              {/* Waveform - cleaner & more elegant */}
              <div className="h-10 flex items-end justify-center gap-[4px] mx-auto max-w-md">
                {[...Array(32)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-[3px] rounded-full transition-all duration-100 ease-out ${
                      recording || isSpeaking
                        ? 'bg-gradient-to-t from-cyan-300 via-purple-400 to-cyan-300'
                        : 'bg-white/10'
                    }`}
                    style={{
                      height: recording || isSpeaking
                        ? `${35 + Math.sin(Date.now() / 120 + i * 1.3) * 65}%`
                        : '6px',
                      opacity: recording || isSpeaking ? 0.5 + Math.random() * 0.5 : 0.25,
                    }}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ======================== */}
        {/*       COMMAND PANEL      */}
        {/* ======================== */}
        <div className="lg:col-span-5 flex flex-col order-1 lg:order-2">
          {/* Status header */}
          <div className="flex justify-between items-center mb-6 px-3">
            <div className="flex items-center gap-4">
              <div className={`w-4 h-4 rounded-full transition-all duration-700 shadow-[0_0_12px] ${
                recording ? "bg-red-600 shadow-red-500/70 animate-ping" :
                isSpeaking ? "bg-purple-500 shadow-purple-600/60 animate-pulse" :
                isProcessing ? "bg-amber-500 shadow-amber-600/60 animate-pulse" :
                "bg-cyan-400 shadow-cyan-500/70"
              }`}></div>
              <span className="text-sm font-black tracking-[0.4em] bg-gradient-to-r from-cyan-200 via-purple-300 to-cyan-200 bg-clip-text text-transparent">
                J.A.R.V.I.S • NEURAL CORE v4.3
              </span>
            </div>
            <div className="text-xs font-mono text-white/50">
              SYSTEM • <span className="text-emerald-400 font-semibold">OPTIMAL</span>
            </div>
          </div>

          {/* Holographic terminal */}
          <div className="flex-1 bg-black/40 backdrop-blur-2xl border border-white/5 rounded-2xl overflow-hidden shadow-[0_0_60px_rgba(0,0,0,0.7)] relative">
            <div className="h-12 bg-gradient-to-r from-white/5 via-transparent to-white/3 border-b border-white/8 flex items-center px-6 text-xs font-mono text-white/50">
              <div className="flex gap-3 mr-8">
                <div className="w-3 h-3 rounded-full bg-red-600/70"></div>
                <div className="w-3 h-3 rounded-full bg-amber-500/60"></div>
                <div className="w-3 h-3 rounded-full bg-emerald-500/60"></div>
              </div>
              neural_interface_session • 0xA7F9K2P
            </div>

            <div className="p-6 md:p-8 lg:p-10 h-full overflow-y-auto font-mono text-sm leading-relaxed">
              {/* User input area */}
              <div className="mb-12">
                <div className="text-xs font-black tracking-widest text-cyan-400/80 mb-3 flex items-center gap-3">
                  <span className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse"></span>
                  VOCAL_INPUT_STREAM
                </div>
                <div className="bg-gradient-to-br from-cyan-950/30 to-black/50 border border-cyan-900/40 p-6 rounded-xl min-h-[100px] text-cyan-50/95 shadow-inner">
                  {heard || <span className="text-white/35 italic opacity-70">Awaiting vocal input...</span>}
                </div>
              </div>

              {/* AI response area */}
              <div>
                <div className="text-xs font-black tracking-widest text-purple-400/80 mb-3 flex items-center justify-end gap-3">
                  SYNTHESIZED_RESPONSE
                  <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
                </div>
                <div className="bg-gradient-to-br from-purple-950/30 to-black/50 border border-purple-900/40 p-6 rounded-xl min-h-[140px] text-purple-50/95 text-right shadow-inner">
                  {response || <span className="text-white/35 italic opacity-70">System standing by. Ready for directive.</span>}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);
}

export default App;