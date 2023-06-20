import telebot

BOT_TOKEN = '5831263373:AAH5ISS8olPT-kLeSP26_CPB0SinPn8PBOE'

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    print(message.chat.id)

bot.polling()