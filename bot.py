#!/usr/bin/env python3
import argparse
import logging
import time
import random
from imgurpython import ImgurClient
from api import TelegramAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class TelegramBot:

    def __init__(self, token, imgur_id, imgur_secret):
        boturl = 'https://api.telegram.org/bot'
        logger.info('Secret bot URL: {0}{1}/'.format(boturl, token))
        self.api = TelegramAPI(url='{0}{1}/'.format(boturl, token))

        # Make this bot self-aware
        myself = self.api.get_me()
        self.id = myself['id']
        self.first_name = myself['first_name']
        self.username = myself['username']

        self.imgur_api = ImgurClient(imgur_id, imgur_secret)

        # Define valid commands
        self.commands = {
            'image': self.image
        }

    def random_gallery(self):
        try:
            gallery = self.imgur_api.gallery_random()
        except:
            logger.exception('Failed to retrieve random gallery')
            gallery = []
        return gallery

    def image_search(self, text, q_any=False):
        q_param = 'q_any' if q_any else 'q_all'
        try:
            gallery = self.imgur_api.gallery_search(
                q=None,
                advanced={q_param: text},
                sort='top',
                window='all')
        except:
            logger.exception('Failed to search')
            gallery = []
        return gallery

    def image(self, text):
        gallery = []
        if text is not None:
            searched = 'Searched for {}'.format(text)
            gallery = self.image_search(text)
        else:
            # No text at all
            searched = 'Searched for a random image'
            gallery = self.random_gallery()
        if not gallery and len(text.split(' ')) > 1:
            # Try searching for any word in text
            or_text = " OR ".join(text.split(' '))
            searched += ', then searched for {}'.format(or_text)
            gallery = self.image_search(text, q_any=True)
        if not gallery:
            searched += '. Found nothing, searched for a random image instead'.format(text)
            gallery = self.random_gallery()
        if gallery:
            image = random.choice(gallery)
            found = image.link
        else:
            found = "nothing"
        returntext = ('{}. found {} out of {} results'.format(
            searched, found, len(gallery)))
        return returntext

    def command(self, command, text):
        logger.info('Parsing command {} with data: {}'.format(command, text))

        # Check if command has been adressed to a specific bot
        split_command = command.split('@')
        if len(split_command) > 1 and split_command[1] != self.username:
            # Not for us
            return None

        clean_command = split_command[0].lstrip('/')
        if clean_command in self.commands:
            return self.commands[clean_command](text)
        return None

    def handle_message(self, message):
        if 'text' in message:
            text = message['text'].split(maxsplit=1)
            command_args = text[1] if len(text) == 2 else None
            return self.command(text[0], command_args)
        return None

    def respond(self, message):
        chat_id = message['chat']['id']
        returntext = self.handle_message(message)
        if returntext:
            try:
                self.api.send_message(chat_id, text=returntext)
            except:
                logger.exception("Failed to send message.")
        return returntext


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--offset', '-o')
    parser.add_argument('--limit', '-l')
    parser.add_argument('--timeout', '-t')
    parser.add_argument('--wait', '-w')
    parser.add_argument('--imgur_id', '-i')
    parser.add_argument('--imgur_secret', '-s')
    parser.add_argument('token')
    args = parser.parse_args()

    bot = TelegramBot(
        token=args.token,
        imgur_id=args.imgur_id,
        imgur_secret=args.imgur_secret)
    offset = args.offset if args.offset else 0
    wait = args.wait if args.wait else 15
    while True:
        logger.info('Waiting {} seconds'.format(wait))
        time.sleep(wait)
        try:
            updates = bot.api.get_updates(
                offset=offset,
                limit=args.limit,
                timeout=args.timeout)
        except:
            logger.exception("Failed to get updates.")
        for update in updates:
            if 'message' in update:
                bot.respond(update['message'])
            if update['update_id'] >= offset:
                offset = update['update_id'] + 1
