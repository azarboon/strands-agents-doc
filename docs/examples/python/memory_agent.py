
# the issue: The agent shows prompt brittleness and poor semantic generalization. 
# It can answer narrowly phrased queries like “what do you know about me,” but fails or stalls on paraphrased intents such as “tell me my preferences.” 
# This indicates shallow intent matching and lack of paraphrase robustness in memory retrieval or tool invocation, rather than true intent abstraction.

## todo next: refine it. when it runs the app. run it, remove duplicate logs and operations. remove the errors


#!/usr/bin/env python3
"""
# 🧠 Memory Agent

A demonstration of using Strands Agents' memory capabilities to store and retrieve information.

## What This Example Shows

This example demonstrates:
- Creating an agent with memory capabilities
- Storing information for later retrieval
- Retrieving relevant memories based on context
- Using memory to create personalized responses

## Usage Examples

Basic usage:
```
python memory_agent.py
```

Import in your code:
```python
from examples.basic.memory_agent import memory_agent

# Store a memory
response = memory_agent("Remember that I prefer tea over coffee")
print(response["message"]["content"][0]["text"])

# Retrieve memories
response = memory_agent("What do I prefer to drink?")
print(response["message"]["content"][0]["text"])
```

## Memory Operations

1. **Store Information**:
   - "Remember that I like hiking"
   - "Note that I have a dog named Max"
   - "I want you to know I prefer window seats"

2. **Retrieve Information**:
   - "What do you know about me?"
   - "What are my hobbies?"
   - "Do I have any pets?"

3. **List All Memories**:
   - "Show me everything you remember"
   - "What memories do you have stored?"
"""

import os
import logging
from dotenv import load_dotenv

from strands import Agent
from strands_tools import mem0_memory, use_llm

logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
load_dotenv()

# Set AWS credentials and configuration
# os.environ["AWS_REGION"] = "us-west-2"
# os.environ['OPENSEARCH_HOST'] = "your-opensearch-host.us-west-2.aoss.amazonaws.com"
## todo azarboon: remove OPENSEARCH_HOST because its not used anywhere in the code
# os.environ['AWS_ACCESS_KEY_ID'] = "your-aws-access-key-id"
# os.environ['AWS_SECRET_ACCESS_KEY'] = "your-aws-secret-access-key"

# For graph memory with Neptune, see:
# https://docs.mem0.ai/open-source/features/graph-memory
# Two options are available for Neptune integration:

# Setup option 1: Neptune Database as graph backend
# os.environ['NEPTUNE_DATABASE_ENDPOINT'] = "your-neptune-host.us-west-2.neptune.amazonaws.com"
# Setup option 2: Neptune Analytics as vector and graph backend
# os.environ['NEPTUNE_ANALYTICS_GRAPH_IDENTIFIER'] = "g-sample-graph-id"
USER_ID = "mem0_user"

# todo azarboon: optionally add the memo stores it on device but can be confiured to store remotely (if thats the case)



# System prompt for the memory agent
MEMORY_SYSTEM_PROMPT = f"""You are a personal assistant that maintains context by remembering user details. 

Capabilities:
- Store new information using mem0_memory tool (action="store")
- Retrieve relevant memories (action="retrieve")
- List all memories (action="list")
- Provide personalized responses

Key Rules:
- Always include user_id={USER_ID} in tool calls
- Be conversational and natural in responses
- Format output clearly
- Acknowledge stored information
- Only share relevant information
- Politely indicate when information is unavailable

Hard rules (non-optional):
- For every user message, you MUST retrieve relevant memories using mem0_memory with action="retrieve" and user_id=USER_ID before responding.
- You MUST do this even if the user input is short, conversational, or differs only by punctuation.
- Never answer questions about the user without retrieving memory first.
"""
## todo azarboon: added the above hard rules to the prompt.

# Create an agent with memory capabilities
memory_agent = Agent(
    model="amazon.nova-lite-v1:0",
    system_prompt=MEMORY_SYSTEM_PROMPT,
    tools=[mem0_memory, use_llm],
)

# Initialize some demo memories
def initialize_demo_memories():
    """Initialize some demo memories to showcase functionality."""
    content = """My name is Alex. I like to travel and stay in Airbnbs rather than hotels. I am planning a trip to Japan next spring. I enjoy hiking and outdoor photography as hobbies. I have a dog named Max. My favorite cuisine is Italian food."""  # noqa
    memory_agent.tool.mem0_memory(action="store", content=content, user_id=USER_ID)

# Example usage
if __name__ == "__main__":
    print("\n🧠 Memory Agent 🧠\n")
    print("This example demonstrates using Strands Agents' memory capabilities")
    print("to store and retrieve information.")
    print("\nOptions:")
    print("  'demo' - Initialize demo memories")
    print("  'exit' - Exit the program")
    print("\nOr try these examples:")
    print("  - Remember that I prefer window seats on flights")
    print("  - What do you know about me?")
    print("  - What are my travel preferences?")
    print("  - Do I have any pets?")


## todo azarboon: updated these but requires further refining due to duplication of logs (and possibly actions)
def is_preference_statement(text: str) -> bool:
    lowered = text.lower().strip()
    return lowered.startswith((
        "i prefer",
        "i like",
        "i love",
        "i plan",
        "i want",
        "i usually",
    ))


if __name__ == "__main__":
    print("\n🧠 Memory Agent 🧠\n")

    while True:
        try:
            user_input = input("\n> ")

            if user_input.lower() == "exit":
                print("\nGoodbye!")
                break

            elif user_input.lower() == "demo":
                initialize_demo_memories()
                print("\nDemo memories initialized!")
                continue

            if is_preference_statement(user_input):
                memory_agent.tool.mem0_memory(
                    action="store",
                    content=user_input,
                    user_id=USER_ID,
                )

            retrieved = memory_agent.tool.mem0_memory(
                action="retrieve",
                query="user preferences and personal facts",
                user_id=USER_ID,
            )

            memory_text = ""
            if isinstance(retrieved, dict):
                for m in retrieved.get("memories", []):
                    content = m.get("content")
                    if content:
                        memory_text += "- " + content + "\n"

            if memory_text.strip():
                final_input = (
                    "Known user information:\n"
                    f"{memory_text}\n"
                    "User message:\n"
                    f"{user_input}"
                )
            else:
                final_input = user_input

            memory_agent(final_input)

        except KeyboardInterrupt:
            print("\n\nExecution interrupted. Exiting...")
            break

        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
