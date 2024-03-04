import os
import json
import uuid
import argparse
import requests
from pydub import AudioSegment
import openai
import uuid
import re

# Deepgram API credentials
DEEPGRAM_API_KEY = "9c3fa8e73e707340d89d6d1453cfa6a91dcb8920"
DEEPGRAM_API_URL = "https://api.deepgram.com/v1/listen"

# OpenAI API key
OPENAI_API_KEY = "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"
OPENAI_API_URL = "https://api.openai.com/v1/engines/gpt-3.5-turbo-instruct/completions"

def transcribe_audio(audio_file):
    print("Transcribing audio file:", audio_file)  # Debugging print

    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}"
    }

    # Send audio file to Deepgram for transcription
    files = {'content': open(audio_file, 'rb')}
    params = {'multichannel': 'true', 'punctuate': 'true', 'paragraphs': 'true'}
    response = requests.post(DEEPGRAM_API_URL, headers=headers, files=files, params=params)

    if response.status_code == 200:
        print("Transcription successful")  # Debugging print

        json_data = response.json()
        channels = json_data.get('results', {}).get('channels', [])
        if not channels:
            print("No channels found in the transcript.")
            return None, None, None

        assistant_transcript = []
        user_transcript = []
        for i, channel in enumerate(channels):
            alternatives = channel.get('alternatives', [])
            if len(alternatives) != 1:
                print(f"Incorrect number of alternatives found in channel {i}. Skipping.")
                continue

            transcript = alternatives[0].get('transcript', '').strip()
            if not transcript:
                continue

            # Assigning transcripts based on channel index
            if i % 2 == 0:
                assistant_transcript.append(transcript)
            else:
                user_transcript.append(transcript)

        if not assistant_transcript and not user_transcript:
            print("No transcripts found in the channels.")
            return None, None, None
        return assistant_transcript[0], user_transcript[0], json_data
    else:
        print("Error occurred during transcription:", response.text)
        return None, None, None

def generate_samples(json_data):
    samples = []
    alternative_1 = json_data['results']['channels'][0]['alternatives'][0]
    alternative_2 = json_data['results']['channels'][1]['alternatives'][0]

    for paragraph_1, paragraph_2 in zip(alternative_1['paragraphs']['paragraphs'], alternative_2['paragraphs']['paragraphs']):
        for sentence_1, sentence_2 in zip(paragraph_1['sentences'], paragraph_2['sentences']):
            # Adding sample for speaker 1
            sample_1 = {
                "id": str(uuid.uuid4()),
                "timestamp": sentence_1['start'],
                "role": "user",
                "content": sentence_1['text'].strip(),
                "tool_calls": [],
                "tool_call_id": None,
                "name": None
            }
            samples.append(sample_1)

            # Adding sample for speaker 2
            sample_2 = {
                "id": str(uuid.uuid4()),
                "timestamp": sentence_2['start'],
                "role": "assistant",
                "content": sentence_2['text'].strip(),
                "tool_calls": [],
                "tool_call_id": None,
                "name": None
            }
            samples.append(sample_2)

    # Sort samples by timestamp
    samples.sort(key=lambda x: x['timestamp'])

    return samples

def generate_prompts(assistant_transcript, user_transcript):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    preface = """Welcome to our AI-driven logistics assistant training data. Our goal is to create an AI assistant specialized in streamlining logistics operations, including call handling, routing, and customer service. Let's dive in and craft prompts that reflect the efficiency, accuracy, and adaptability required for seamless logistics management.\n\n"""

    with open("prompts.jsonl", 'w') as f:
        f.write(preface)
        
        # Generate prompts for the assistant
        assistant_prompt_text = "Context: In this scenario, you are training an AI-driven logistics assistant to handle customer inquiries and provide assistance with various logistics operations. The assistant should be proficient in gathering information, providing options, and confirming decisions to ensure a successful customer assistance operation.\n\n" + "Assistant: " + assistant_transcript
        data = {
            "prompt": assistant_prompt_text,
            "max_tokens": 1000
        }
        response = requests.post(OPENAI_API_URL, headers=headers, json=data)
        if response.status_code == 200:
            generated_prompt = response.json()["choices"][0]["text"]
            f.write(generated_prompt)
            f.write("\n") 
        else:
            print("Error occurred during assistant prompt generation:", response.text)

        # Generate prompts for the user
        user_prompt_text = "Context: In this scenario, you are training an AI-driven logistics simulator to imitate a customer inquiry and request assistance with various logistics operations. The user should have a well-defined narrow logistics question, know their options, and be respectful.\n\n" + "User: " + user_transcript
        data = {
            "prompt": user_prompt_text,
            "max_tokens": 1000
        }
        response = requests.post(OPENAI_API_URL, headers=headers, json=data)
        if response.status_code == 200:
            generated_prompt = response.json()["choices"][0]["text"]
            f.write(generated_prompt)
            f.write("\n") 
        else:
            print("Error occurred during user prompt generation:", response.text)

    print("Prompts saved to: prompts.jsonl")

def main():
    parser = argparse.ArgumentParser(description="Transcribe audio file and generate JSONL samples")
    parser.add_argument("audio_file", help="Path to the audio file")
    parser.add_argument("-p", "--prompts", default="prompts.jsonl", help="Path to the output prompts JSONL file")

    args = parser.parse_args()

    # Transcribe audio
    assistant_transcript, user_transcript, json_data = transcribe_audio(args.audio_file)
    if not json_data:
        return

    # Generate samples
    samples = generate_samples(json_data)
    with open("output.jsonl", 'w') as f:
        for sample in samples:
            f.write(json.dumps(sample) + '\n')
    print("Samples saved to output.jsonl")

    # Generate prompts
    generate_prompts(assistant_transcript, user_transcript)

# Execute the main function if this script is run directly
if __name__ == "__main__":
    main()

