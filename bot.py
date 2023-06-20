import telebot
from telebot import types
import openai
from time import time, sleep
import textwrap
import sys
import yaml


###     file operations


def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()


def save_yaml(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, allow_unicode=True)


def open_yaml(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    return data


###     API functions


def chatbot(conversation, model="gpt-3.5-turbo", temperature=0):
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=conversation, temperature=temperature)
            text = response['choices'][0]['message']['content']
            return text, response['usage']['total_tokens']
        except Exception as oops:
            print(f'\n\nError communicating with OpenAI: "{oops}"')
            if 'maximum context length' in str(oops):
                a = conversation.pop(0)
                print('\n\n DEBUG: Trimming oldest message')
                continue
            retry += 1
            if retry >= max_retry:
                print(f"\n\nExiting due to excessive errors in API: {oops}")
                exit(1)
            print(f'\n\nRetrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)

###     CHAT functions


def compose_conversation(ALL_MESSAGES, text, system_message):
    # continue with composing conversation and response
    ALL_MESSAGES.append({'role': 'user', 'content': text})
    conversation = list()
    conversation += ALL_MESSAGES
    conversation.append({'role': 'system', 'content': system_message})
    return conversation

def generate_chat_response(ALL_MESSAGES, conversation):
    # generate a response
    response, tokens = chatbot(conversation)
    if tokens > 7500:
        return('Unfortunately, this conversation has become too long, so the survey must come to an end. Program will end in 5 seconds.')
    ALL_MESSAGES.append({'role': 'assistant', 'content': response})
    print('\n\n\n\nCHATBOT:\n')
    formatted_lines = [textwrap.fill(line, width=120, initial_indent='    ', subsequent_indent='    ') for line in response.split('\n')]
    formatted_text = '\n'.join(formatted_lines)
    return(formatted_text)

BOT_TOKEN = '5948606290:AAG2-CjeI1YpJIQkDScA_nK7QMIqPsqcAuI'

bot = telebot.TeleBot(BOT_TOKEN)

research_question = open_file('question.txt')
openai.api_key = open_file('key_openai.txt').strip()
system_message = open_file('system.txt').replace('<<QUESTION>>', research_question)
ALL_MESSAGES = list()
start_time = time()

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    msg = bot.reply_to(message, '\n\n****** IMPORTANT: ******\n\nType /done to exit\n\nSurvey Question:... %s \n\nTo get started, please type in your name:' % research_question)
    bot.register_next_step_handler(msg, process_name_step)


def process_name_step(message):
    try:
        username = message.text
        if username == '/done':
            msg = bot.reply_to(message, '\n\n\nThank you for participating in this survey! Your results have been saved. Program will exit in 5 seconds.')
        else:
            global filename
            filename = f"chat_{start_time}_{username}.yaml"
            text = f"Hello, my name is {username}."
            conversation = compose_conversation(ALL_MESSAGES, text, system_message)
            openAI_response = generate_chat_response(ALL_MESSAGES, conversation)
            msg = bot.reply_to(message, openAI_response)
            #bot.register_next_step_handler(msg, process_thoughts_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')

    @bot.message_handler(func=lambda message: True)
    def process_thoughts_step(message):
        try:
            text = message.text
            if text == '/done':
                bot.reply_to(message, '\n\n\nThank you for participating in this survey! Your results have been saved. Program will exit in 5 seconds.')
            else:
                conversation = compose_conversation(ALL_MESSAGES, text, system_message)
                save_yaml(f'chat_logs/{filename}', ALL_MESSAGES)
                
                openAI_response = generate_chat_response(ALL_MESSAGES, conversation)
                bot.reply_to(message, openAI_response)
                save_yaml(f'chat_logs/{filename}', ALL_MESSAGES)
                #bot.register_next_step_handler(msg, process_thoughts_step)
        except Exception as e:
            bot.reply_to(message, 'oooops')
            
bot.enable_save_next_step_handlers(delay=2)

bot.load_next_step_handlers()

bot.infinity_polling()