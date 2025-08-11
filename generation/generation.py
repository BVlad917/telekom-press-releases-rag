from collections import defaultdict

from openai import OpenAI, OpenAIError

from constants import *


def group_chunks_by_source(context_chunks: list[dict]) -> dict:
    """
    Group retrieved chunks by their source URL.
    """
    grouped_chunks = defaultdict(list)

    for chunk in context_chunks:
        source_link = chunk['source_link']
        grouped_chunks[source_link].append(chunk)
    return grouped_chunks


def build_prompt(user_question: str, context_chunks: list[dict]) -> str:
    """
    Build the augmented prompt for the LLM.
    """
    assert len(context_chunks) > 0, "The LLM needs at least one context chunk to generate an answer to the user's question."

    grouped_chunks = group_chunks_by_source(context_chunks)

    # Number the sources for clear citation
    context_str = ""
    for i, (url, chunk_list) in enumerate(grouped_chunks.items()):
        context_str += f"[Source {i + 1}]:\n"
        context_str += f'URL: {url}\n'
        context_str += f"Published Date: {chunk_list[0]['publish_date']}\n"
        context_str += "Relevant Content:\n"
        for chunk in chunk_list:
            context_str += f'- "{chunk["content"]}"\n'
        context_str += "\n"

    prompt = f"""
You are a highly analytical assistant. Your task is to answer a user's question based *only* on the provided context.

Follow these instructions precisely:
1.  First, write a concise, synthesized answer to the user's question using information from the sources below.
2.  For each piece of information you use, you **must** include a citation marker in the format `[Source X]` where X is the number of the source you are referencing.
3.  After the answer, create a "Sources Used" section.
4.  In the "Sources Used" section, list *only* the sources you actually cited in your answer. For each source, provide its number and its full URL.
5.  If the provided context does not contain enough information to answer the question, you must state: "Based on the provided context, I cannot answer this question."

---
CONTEXT:
{context_str}
---

USER'S QUESTION:
"{user_question}"

---

YOUR STRUCTURED RESPONSE:
"""
    return prompt


def get_llm_answer(prompt):
    """
    Send the prompt to the OpenAI API and get the answer.
    """
    try:
        client = OpenAI(api_key=OPENAI_KEY)

        response = client.chat.completions.create(
            model=OPENAI_LLM_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_OUTPUT_TOKENS
        )
        return response.choices[0].message.content
    except OpenAIError as e:
        print(f"Error while initializing OpenAI API: {e}")
        return "You must set the OpenAI API key."
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "Sorry, I encountered an error while generating the answer."
