import os
import threading

import telebot
from telebot import types

from src.common import config

class TelegramBot():
    def __init__(self):
        API_KEY = os.getenv('BOT_TOKEN')
        self.CHAT_ID = int(os.getenv('CHAT_ID'))
        self.telebot = telebot.TeleBot(API_KEY)
        self.waiting_response = False
        self.manual_replies = []
        config.telegram = self
        @self.telebot.message_handler(func=lambda message: self.waiting_response and len(self.manual_replies) < 4)
        def handle_message(message):
            self.manual_replies.append(message.text)
        self.markup = types.ReplyKeyboardMarkup()
        up = types.KeyboardButton('up')
        down = types.KeyboardButton('down')
        left = types.KeyboardButton('left')
        right = types.KeyboardButton('right')

        self.markup.row(up)
        self.markup.row(left, down, right)
    
        self.ready = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True
    
    def start(self):
        """
        Starts this Telegram object's thread.
        :return:    None
        """

        print('\n[~] Started Telegram Bot')
        self.thread.start()
        
    def _main(self):
        self.ready = True
        # Run bot
        self.telebot.infinity_polling()

    def send_rune_video(self, video_path):
        video = open(video_path, 'rb')
        self.telebot.send_video(self.CHAT_ID, video, reply_markup=self.markup)