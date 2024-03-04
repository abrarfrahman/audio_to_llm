# audio_to_llm
Logistics support LLM bot with Deepgram

In this challenge, the goal is to build a pipeline that let’s you convert audio files featuring a phone conversation into an LLM. You don’t need to actually finetune an LLM, but your job is to create training samples in the format that OpenAI expects (JSONL).

These are a couple of example calls. In each of those calls, there’s gonna be an `assistant` who is the person getting the call, and the `user` who is the person that calls in asking about a load they saw online.

To run, `cd` into the target directory and then `python3 audio_to_llm.py file/path/here`
