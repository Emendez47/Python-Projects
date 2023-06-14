import openai
import gradio

openai.api_key = ''  # Enter api key

messages = [{"role": "system",
             "content": "You are a advisor for startup."}]


def CustomChatGPT(user_input):
    messages.append({"role": "user", "content": user_input})
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )
    ChatGPT_reply = response["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": ChatGPT_reply})
    return ChatGPT_reply


demo = gradio.Interface(fn=CustomChatGPT, inputs="text",
                        outputs="text", title="Chat Gpt")

demo.launch(share=True)
