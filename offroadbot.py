import os
import telebot
import numpy as np

BOT_TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    sent_msg = bot.send_message(
        message.chat.id, "Hello! I am an off-road calculator for Maplestory R. Please tell me what the returns are and I will calculate if it is possible to win as well as the optimal bet size. Please input in an array of this form: [1, 2, 3, 4, 5, 6]")
    bot.register_next_step_handler(
        sent_msg, calculate)

@bot.message_handler(func=lambda message: True)
def calculate(message):
    try:
        text = message.text
        # convert text to a numpy array of integers
        returns = np.array(list(map(int, text.strip('[]').split(','))))

        # calculate if arbitrage is possible
        odds = 1/returns
        if np.sum(odds) < 1:
            bot.reply_to(message, "Possible arbitrage!")
        else:
            bot.reply_to(message, "No winnings available!")
            return

        # calculate optimal stake
        stake = np.ones(6)
        win = np.zeros(6)
        for i in range(6):
            win[i] = winnings(returns[i], stake[i])
        arbitrage = False
        total_cost = np.sum(stake)
        while total_cost < 30:
            if np.any(stake>12):
                break
            if np.all(win>=total_cost):
                arbitrage = True
                break
            for i in range(6):
                if win[i] < total_cost:
                    stake[i] += 1
                    win[i] = winnings(returns[i], stake[i])
            total_cost = np.sum(stake)
        if arbitrage:
            bot.reply_to(message, f"Arbitrage found! Optimal stake:{stake}")
        else:
            bot.reply_to(message, "No arbitrage found!")

    except ValueError:
        bot.reply_to(message, "Please make sure to input numbers in a proper array format like [1, 2, 3, 4, 5, 6].")
    
def winnings(ret, stake):
    if stake > 4:
        return ret*stake - np.ceil((stake-4)/8)
    else:
        return ret*stake

bot.infinity_polling()