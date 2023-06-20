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


###     CHAT FUNCTIONS


def get_user_input():
    # get user input
    # text = input('\n\n\nUSER:\n\n')
    
    
    # get user input
    text = input('\n\n\nUSER:\n\n')
    
    # check if scratchpad updated, continue
    if 'DONE' in text:
        print('\n\n\nThank you for participating in this survey! Your results have been saved. Program will exit in 5 seconds.')
        sleep(5)
        exit(0)
    if text == '':
        # empty submission, probably on accident
        None
    else:
        return text


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
        print('Unfortunately, this conversation has become too long, so the survey must come to an end. Program will end in 5 seconds.')
        sleep(5)
        exit(0)
    ALL_MESSAGES.append({'role': 'assistant', 'content': response})
    print('\n\n\n\nCHATBOT:\n')
    formatted_lines = [textwrap.fill(line, width=120, initial_indent='    ', subsequent_indent='    ') for line in response.split('\n')]
    formatted_text = '\n'.join(formatted_lines)
    print(formatted_text)


if __name__ == '__main__':
    # instantiate chatbot, variables
    research_question = open_file('question.txt')
    openai.api_key = open_file('key_openai.txt').strip()
    system_message = open_file('system.txt').replace('<<QUESTION>>', research_question)
    ALL_MESSAGES = list()
    start_time = time()
    
    # get username, start conversation
    print('\n\n****** IMPORTANT: ******\n\nType DONE to exit\n\nSurvey Question: %s' % research_question)
    username = input('\n\n\nTo get started, please type in your name: ').strip()
    filename = f"chat_{start_time}_{username}.yaml"
    text = f"Hello, my name is {username}."
    conversation = compose_conversation(ALL_MESSAGES, text, system_message)
    generate_chat_response(ALL_MESSAGES, conversation)

    while True:
        text = get_user_input()
        if not text:
            continue
        
        conversation = compose_conversation(ALL_MESSAGES, text, system_message)
        save_yaml(f'chat_logs/{filename}', ALL_MESSAGES)
        
        generate_chat_response(ALL_MESSAGES, conversation)
        save_yaml(f'chat_logs/{filename}', ALL_MESSAGES)