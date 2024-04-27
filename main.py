import os
import telebot
import numpy as np
from dotenv import load_dotenv
import atexit
import tempfile

# Path for the lock file
temp_dir = tempfile.gettempdir()
lock_file_path = os.path.join(temp_dir, 'bot.lock')

# Function to check if another instance is running
def check_lock():
    if os.path.exists(lock_file_path):
        print("Another instance is already running.")
        exit(0)
    else:
        open(lock_file_path, 'w').close()

# Ensure only one instance runs
check_lock()

load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("No Telegram bot token provided.")

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
            win[i] = returns[i]*stake[i]
        arbitrage = False
        total_cost = np.sum(stake) + np.sum(np.ceil((stake-4)/8)) # include cost of going over bet size = 4
        while total_cost < 36:
            # maximum bet size = 12
            if np.any(stake>12):
                break
            # check if all bets will be positive EV
            if np.all(win>=total_cost):
                arbitrage = True
                break
            # update values for next iteration
            for i in range(6):
                if win[i] < total_cost:
                    stake[i] += 1
                    win[i] = returns[i]*stake[i]
            total_cost = np.sum(stake) + np.sum(np.ceil((stake-4)/8))

        # output if arbitrage is possible and what the optimal stake is
        if arbitrage:
            # simple heuristic to increase winnings if the bet sizes are small
            if np.all(stake<=1):
                stake *= 4
            elif np.all(stake<=2):
                stake *= 2
            stake *= 50 # multiplied by 50 to match in-game betting sizes
            stake = stake.astype(int).tolist()
            bot.reply_to(message, f"Arbitrage found! Optimal bet size: {stake}") 
        else:
            bot.reply_to(message, "No arbitrage found!")

    except ValueError:
        bot.reply_to(message, "Please make sure to input numbers in a proper array format like [1, 2, 3, 4, 5, 6].")

bot.infinity_polling()

# Code to remove the lock file on exit
def remove_lock():
    os.remove(lock_file_path)

atexit.register(remove_lock)