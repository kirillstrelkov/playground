import openai

# Step 1: Point the OpenAI client to your local LM Studio server
# The default base URL for LM Studio's API is http://localhost:1234/v1
# We also set a dummy API key, as it's not required for a local server
client = openai.OpenAI(
    base_url="http://172.24.80.1:1234/v1",
    api_key="lm-studio",  # Can be any string, but required by the library
)


def get_local_model_response(prompt, model_name):
    """
    Sends a chat completion request to the local LM Studio server.

    Args:
        prompt (str): The user's input prompt.
        model_name (str): The name of the model currently loaded in LM Studio.
    """
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )

        # Step 3: Extract and print the model's response
        completion.choices[0].message.content

    except Exception:
        pass
