import speech_recognition as sr
import requests
from gtts import gTTS
import os
import time

def speak(text):
    try:
        tts = gTTS(text=text, lang='en')
        filename = "voice.mp3"
        tts.save(filename)
        os.system(f"start {filename}" if os.name == 'nt' else f"afplay {filename}")  # macOS: afplay, Windows: start
        time.sleep(1)  # wait before continuing
    except Exception as e:
        print("Speech error:", e)

def listen():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"🗣️ You said: {text}")
        return text.lower()
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
        return ""
    except sr.RequestError:
        speak("Network error.")
        return ""

def get_recipe_info(dish_name):
    url = "http://localhost:5000/get-recipe"
    res = requests.post(url, json={"dish": dish_name})
    return res.json()

def scrape_recipe(url):
    scrape_url = "http://localhost:5000/scrape"
    res = requests.post(scrape_url, json={"url": url})
    return res.json()

def main():
    speak("Hi, what would you like to cook today?")
    dish = listen()

    if not dish:
        speak("Please try again.")
        return

    recipe_data = get_recipe_info(dish)
    if "error" in recipe_data:
        speak("Sorry, I couldn't find that recipe.")
        return

    url = recipe_data["response"]["link"]
    speak(f"I found a recipe for {dish}. Let me fetch the ingredients.")
    scraped = scrape_recipe(url)

    if "error" in scraped:
        speak("Sorry, I couldn't extract the recipe steps.")
        return

    ingredients = scraped["ingredients"]
    instructions = scraped["instructions"]

    # Ask user if they have all ingredients
    speak("Here's what you'll need:")
    for item in ingredients:
        speak(item)

    speak("Do you have all the ingredients?")
    response = listen()

    if "yes" not in response:
        speak("Okay, let me know when you're ready.")
        return

    speak("Great! Let's start cooking.")
    for i, step in enumerate(instructions, 1):
        speak(f"Step {i}: {step}")
        speak("Say next when you are ready.")
        while True:
            nxt = listen()
            if "next" in nxt:
                break

    speak("Well done! You've completed the recipe.")

if __name__ == "__main__":
    main()
