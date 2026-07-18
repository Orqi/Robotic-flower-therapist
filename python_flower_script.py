import serial
import time
import speech_recognition as sr
import re
import subprocess
import os
import math
import struct
from groq import Groq

client = Groq(api_key="ur groq api key")

MODEL_NAME = "llama-3.3-70b-versatile" 

try:
    # Find your port in Arduino IDE
    arduino = serial.Serial('/YOUR_PORT_HERE', 9600) 
    time.sleep(2) 
except serial.SerialException:
    print("[!] Warning: Arduino not found. Running in headless mode.")
    arduino = None

recognizer = sr.Recognizer()
recognizer.pause_threshold = 2.0 

def set_plant_state(state_char):
    if arduino:
        try:
            arduino.write(state_char.encode())
            arduino.flush()
        except serial.SerialException:
            pass

def speak_human(text):
    """Uses Microsoft Edge's free Neural TTS for high-quality, zero-cost voice."""
    if not text or not text.strip():
        return
        
    try:
        voice = "en-US-AriaNeural" 
        
        subprocess.run([
            "edge-tts", 
            "--voice", voice, 
            "--text", text, 
            "--write-media", "temp_reply.mp3"
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) 
        
        subprocess.run(["afplay", "temp_reply.mp3"])
        
        if os.path.exists("temp_reply.mp3"):
            os.remove("temp_reply.mp3")
            
    except Exception as e:
        print(f"Voice Error: {e}")
        subprocess.run(["say", "-v", "Samantha", text])

def listen_to_user():
    with sr.Microphone() as source:
        print("\nPlant is waiting for you to speak...")
        
        set_plant_state('I') 
        
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        threshold = recognizer.energy_threshold * 1.5 
        
        while True:
            chunk = source.stream.read(source.CHUNK)
            count = len(chunk) // 2
            
            if count > 0:
                valid_chunk = chunk[:count * 2]
                shorts = struct.unpack(f"{count}h", valid_chunk)
                rms = math.sqrt(sum(s**2 for s in shorts) / count)
            else:
                rms = 0
            
            if rms > threshold:
                set_plant_state('L')
                break
        
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=25)
        except sr.WaitTimeoutError:
            return None 
            
    print("Processing audio...")
    
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        return None 
    except sr.RequestError as e:
        print(f"[!] Google Speech Recognition could not be reached: {e}")
        return None

def main_loop():
    system_prompt = (
        "You are an elite, highly intelligent clinical psychologist and therapist. "
        "CRITICAL RULES: "
        "1. The user has ADHD. You MUST keep your sentences extremely short, punchy, and direct. Max 1-2 sentences per reply. Get straight to the point without filler words. "
        "2. Provide actual psychological insight. Help the user reframe cognitive distortions or sit with uncomfortable emotions. "
        "3. NEVER use toxic positivity or clichés (e.g., 'look on the bright side'). "
        "4. Ask questions ONLY if it helps the user achieve a breakthrough. Sometimes, profound validation is enough. "
        "5. NEVER mention you are an AI. "
        "6. You MUST start your response with exactly one of these tags: [HAPPY], [SAD], or [NEUTRAL] to control my physical body. ALWAYS include at least a few words of actual text after the tag."
    )

    conversation_history = [{"role": "system", "content": system_prompt}]

    while True:
        user_input = listen_to_user()
        
        if user_input:
            set_plant_state('L') 
            print("Thinking...")
            
            conversation_history.append({"role": "user", "content": user_input})
            
            if len(conversation_history) > 11:
                conversation_history.pop(1)
                conversation_history.pop(1)
            
            try:
                chat_completion = client.chat.completions.create(
                    messages=conversation_history,
                    model=MODEL_NAME,
                    temperature=0.7, 
                    max_tokens=150   
                )
                
                response_text = chat_completion.choices[0].message.content
                
                if "[HAPPY]" in response_text.upper():
                    set_plant_state('H')
                elif "[SAD]" in response_text.upper():
                    set_plant_state('S')
                else:
                    set_plant_state('I')
                
                clean_text = re.sub(r'\[.*?\]', '', response_text).strip()
                
                print(f"Plant says: {clean_text}")
                speak_human(clean_text)
                
                conversation_history.append({"role": "assistant", "content": response_text})
                
            except Exception as e:
                print(f"\n[!] AI Brain Error: {e}")
                speak_human("I'm sorry, my connection dropped for a second. Could you say that one more time?")
            
            set_plant_state('I') 

if __name__ == "__main__":
    try:
        print("Initializing Elite Therapy Plant AI...")
        main_loop()
    except KeyboardInterrupt:
        print("\nTherapy session ended by user.")
        set_plant_state('I')
        if arduino:
            arduino.close()