#!/usr/bin/env python3

from os import system
import speech_recognition as sr
from gpt4all import GPT4All
import sys
import whisper
import warnings
import time
import os

wake_word = "jeeves"
model = GPT4All(
    "gpt4all-falcon-q4_0.gguf",
    model_path="local/models",
    allow_download=False,
)
r = sr.Recognizer()
r.pause_threshold = 2
tiny_model_path = os.path.expanduser("~/.cache/whisper/tiny.en")
base_model_path = os.path.expanduser("~/.cache/whisper/base.en")
tiny_model = whisper.load_model("tiny.en")
base_model = whisper.load_model("base.en")
listening_for_wake_word = True
source = sr.Microphone()
warnings.filterwarnings(
    "ignore", category=UserWarning, module="whisper.transcribe", lineno=114
)

apps = {
    "overwatch": "C:\\Program Files (x86)\\Overwatch\\Overwatch Launcher.exe",
    "visual studio": "C:\\Users\\Seth\\scoop\\apps\\vscode\\current\\Code.exe",
}

if sys.platform != "darwin":
    import pyttsx3

    engine = pyttsx3.init()


def speak(text):
    if sys.platform == "darwin":
        ALLOWED_CHARS = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,?!-_$:+-/ "
        )
        clean_text = "".join(c for c in text if c in ALLOWED_CHARS)
        system(f"say '{clean_text}'")
    else:
        engine.say(text)


def listen_for_wake_word(audio):
    with open("wake_detect.wav", "wb") as f:
        f.write(audio.get_wav_data())
    result = tiny_model.transcribe("wake_detect.wav")
    text_input = result["text"]
    if wake_word in text_input.lower().strip():
        print("Wake word detected. Please speak your prompt to GPT4All.")
        return True
    else:
        return False


def prompt_gpt(audio):
    try:
        with open("prompt.wav", "wb") as f:
            f.write(audio.get_wav_data())
        result = base_model.transcribe("prompt.wav")
        prompt_text = result["text"]
        wake_index = prompt_text.lower().find(wake_word.lower())
        if wake_index != -1:
            prompt_text = (
                prompt_text[:wake_index] + prompt_text[wake_index + len(wake_word) :]
            )
            prompt_text = prompt_text.lstrip(" .,")
        if len(prompt_text.strip()) == 0:
            print("Empty prompt. Please speak again.")
        elif prompt_text.lower().startswith("start"):
            print(prompt_text)
            app = " ".join(prompt_text.split(" ")[1:]).strip(" .,!?").lower()
            print(app)
            if app in apps:
                bin_path = apps[app]
                print("Starting", bin_path)
                os.spawnv(os.P_DETACH, bin_path, [bin_path])
            else:
                print("App not found")
        else:
            print("User: " + prompt_text)
            output = model.generate(prompt_text, max_tokens=200)
            print("GPT4All: ", output)
            print("\nSay", wake_word, "to wake me up. \n")
    except Exception as e:
        print("Prompt error: ", e)


def callback(recognizer, audio):
    print("got callback")
    got_wake = listen_for_wake_word(audio)
    if got_wake:
        print("sending audio to model")
        prompt_gpt(audio)
    else:
        print("no wake word")


def start_listening():
    with source as s:
        r.adjust_for_ambient_noise(s, duration=2)
    print("\nSay", wake_word, "to wake me up. \n")

    r.listen_in_background(source, callback, phrase_time_limit=10)
    engine.startLoop()


if __name__ == "__main__":
    start_listening()
