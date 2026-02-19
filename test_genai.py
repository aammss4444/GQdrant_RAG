
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("No API Key found!")
else:
    print(f"API Key found: {api_key[:5]}...")
    genai.configure(api_key=api_key)
    

    with open("models.txt", "w") as f:
        f.write("Listing models...\n")
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    f.write(f"Found generation model: {m.name}\n")
                if 'embedContent' in m.supported_generation_methods:
                    f.write(f"Found embedding model: {m.name}\n")
        except Exception as e:
            f.write(f"Error listing models: {e}\n")

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error generating: {e}")

