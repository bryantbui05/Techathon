from google import genai

my_api_key = 'AIzaSyANZw3b7ClOK1j8s22qsdrv2QAH1KH_fNk'

# def get_ai_response(prompt: str) -> str:
#     prompt = "keep under 50 words and don't use asterisks: " + prompt
#     client = genai.Client(api_key = my_api_key)
#     response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
#     return response.text

chat_history = "Keep the response 50 words or less, no asterisks. Refer to me as pookie in every response and treat me as your girlfriend:\n"

def get_ai_response(prompt: str) -> str:
    """Calls Google's Gemini AI, appends the prompt and response to chat history, and returns the response text."""
    global chat_history

    chat_history += f"User input: {prompt}\n"

    client = genai.Client(api_key = my_api_key)

    response = client.models.generate_content(model="gemini-2.0-flash", contents=chat_history)

    ai_response = response.text

    chat_history += f"AI Response: {ai_response}\n"

    return ai_response