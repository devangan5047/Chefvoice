import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import os
import pygame

# Configure the Gemini API with your key
API_KEY = 'AIzaSyB0KQNuMmZyV2cVfKrgfuscnOJfh475IT0' 
genai.configure(api_key=API_KEY)

def speak(text):
    """Converts text to speech and plays it using pygame."""
    try:
        tts = gTTS(text=text, lang='en')
        filename = 'response.mp3'
        tts.save(filename)

        # Use pygame to play the audio
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        # Wait for the audio to finish playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload() # Unload the music to free the file
        os.remove(filename) # Clean up the audio file

        print(f"ChefVoice AI: {text}")
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
        
def listen_for_command():
    """Listens for user's voice command and converts it to text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for your command...")
        audio = r.listen(source)
        try:
            command = r.recognize_google(audio)
            print(f"You said: {command}")
            return command
        except sr.UnknownValueError:
            speak("Sorry, I did not understand that.")
            return None
        except sr.RequestError:
            speak("Sorry, my speech service is down.")
            return None
        
def generate_response(command):
    """Sends the command to the Gemini model and gets a structured recipe response."""
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    # The new prompt is very specific about the output format.
    prompt = f"""
    You are ChefVoice, a hands-free AI cooking assistant.
    A user has asked for a recipe for: "{command}"

    Generate the recipe with the following strict format:
    - Start with a title for the recipe.
    - Use the heading '## Ingredients' followed by a bulleted list of ingredients.
    - Use the heading '## Instructions' followed by a numbered list of step-by-step instructions.
    - Do not add any conversational text before the title or after the instructions.
    """
    
    try:
        response = model.generate_content(prompt)
        print("--- AI Response Received ---")
        print(response.text)
        print("--------------------------")
        return response.text
    except Exception as e:
        print(f"Error generating response: {e}")
        return None
    
    
def parse_recipe(recipe_text):
    """Splits the recipe text into ingredients and instructions."""
    try:
        # Split the text at the '## Instructions' heading
        parts = recipe_text.split('## Instructions')
        ingredients_part = parts[0]
        instructions_part = parts[1]

        # Clean up the ingredients part
        ingredients = ingredients_part.replace('## Ingredients', '').strip()

        # Clean up and split the instructions into a list of steps
        instructions = [step.strip() for step in instructions_part.strip().split('\n') if step.strip()]
        
        return ingredients, instructions
    except Exception as e:
        print(f"Error parsing recipe: {e}")
        return None, None

def wait_for_confirmation(prompt=""):
    """Listens for confirmation keywords like 'ready', 'next', or 'repeat'."""
    if prompt:
        speak(prompt)
        
    while True:
        command = listen_for_command()
        if command:
            command = command.lower()
            # Keywords to move to the next step
            if any(word in command for word in ["yes", "ready", "okay", "next", "proceed"]):
                return "next"
            # Keyword to repeat the last step
            if "repeat" in command:
                return "repeat"
            # Keyword to stop the process
            if any(word in command for word in ["stop", "exit", "cancel"]):
                return "stop"
            
            speak("Sorry, I didn't catch that. Please say 'ready' to continue, 'repeat' to hear it again, or 'stop' to cancel.")
                
def main():
    """The main function to run the ChefVoice assistant."""
    pygame.mixer.init()
    speak("Hello! I am ChefVoice. What would you like to cook today?")
    
    while True:
        # 1. Listen for a recipe request
        recipe_request = listen_for_command()
        if not recipe_request:
            continue # If nothing was heard, listen again

        if "exit" in recipe_request.lower() or "goodbye" in recipe_request.lower():
            speak("Happy cooking. Goodbye!")
            break
            
        speak(f"Great! Finding a recipe for {recipe_request}.")
        
        # 2. Generate and parse the recipe
        full_recipe_text = generate_response(recipe_request)
        if not full_recipe_text:
            speak("I'm sorry, I couldn't find a recipe for that. Please try another dish.")
            continue
            
        ingredients, instructions = parse_recipe(full_recipe_text)
        if not ingredients or not instructions:
            speak("I had trouble understanding the recipe format. Let's try a different one.")
            continue
        
        # 3. Read ingredients and wait for confirmation
        speak("I have the recipe. First, I'll list the ingredients.")
        speak(ingredients)
        
        action = wait_for_confirmation("Let me know when you are ready to start cooking.")
        
        if action != "next":
            speak("Okay, cancelling the recipe. What would you like to cook next?")
            continue

        # 4. Loop through instructions step-by-step
        speak("Excellent! Let's begin.")
        
        instruction_index = 0
        while instruction_index < len(instructions):
            current_step = instructions[instruction_index]
            speak(current_step)
            
            # Don't ask for confirmation on the very last step
            if instruction_index < len(instructions) - 1:
                action = wait_for_confirmation("Are you ready for the next step?")
                
                if action == "next":
                    instruction_index += 1 # Move to next step
                elif action == "repeat":
                    speak("No problem. Here is the last step again.")
                    # The index doesn't change, so the loop will repeat the same step
                elif action == "stop":
                    speak("Okay, stopping here. Let me know if you want to cook something else.")
                    break # Exit the instruction loop
            else:
                instruction_index += 1 # End the loop after the last step

        if instruction_index == len(instructions): # Check if we completed all steps
            speak("You've completed the final step. Enjoy your meal!")

        speak("What would you like to cook next?")

if __name__ == "__main__":
    main()