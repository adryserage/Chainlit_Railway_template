from llm_api import openai_chatbot_chain, ModelProvider, llm_client
import chainlit as cl

#|--------------------------------------------------------------------------|
#|                            On Boarding                                   |
#|--------------------------------------------------------------------------|
@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set(
        "message_history",
        [{"role": "system", "content": "You are a helpful assistant."}],
    )
    app_user = cl.user_session.get("user")
    await cl.Message(f"Hello User").send()

#|--------------------------------------------------------------------------|
#|                               Chat                                       |
#|--------------------------------------------------------------------------|
@cl.on_message
async def main(user_input: cl.Message):
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": user_input.content})

    # Create message with loading state
    llm_output = cl.Message(content="🤔 Thinking...", author="Assistant")
    await llm_output.send()
    # Get response stream
    stream = await openai_chatbot_chain(message_history)
    
    # Clear thinking message and start streaming response
    llm_output.content = ""
    await llm_output.update()
    
    async for chunk in stream:
        content = None
        if llm_client.config.provider == ModelProvider.OPENAI:
            content = chunk.choices[0].delta.content
        elif llm_client.config.provider == ModelProvider.ANTHROPIC:
            if chunk.type == 'content_block_delta':
                content = chunk.text
        elif llm_client.config.provider == ModelProvider.GEMINI:
            content = chunk.text
            
        if content:
            await llm_output.stream_token(content)

    message_history.append({"role": "assistant", "content": llm_output.content})
    await llm_output.update()