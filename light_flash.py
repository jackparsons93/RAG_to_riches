import speech_recognition as sr
import PiMotor
import time
import threading

# Initialize the motor
m4 = PiMotor.Motor("MOTOR4", 1)

# Function to flash the light on Motor 4
def flash_light():
    while True:
        m4.forward(100)  # Turn the light on
        time.sleep(0.05)  # Keep the light on for 50ms
        m4.stop()         # Turn the light off
        time.sleep(0.05)  # Keep the light off for 50ms

# Function to listen for the "activate lights" command
def listen_for_command():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    while True:
        with microphone as source:
            print("Listening for command...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            command = recognizer.recognize_google(audio).lower()
            print(f"Recognized command: {command}")

            if "activate lights" in command:
                print("Activating lights...")
                threading.Thread(target=flash_light).start()  # Start flashing the light in a new thread
                break  # Exit the loop after activating lights

        except sr.UnknownValueError:
            print("Sorry, I did not understand that.")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")

if __name__ == "__main__":
    listen_for_command()
