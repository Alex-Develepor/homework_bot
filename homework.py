import json
import logging
import os
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler = RotatingFileHandler(
    'my_logger.log',
    maxBytes=50000000,
    backupCount=5
)
handler.setFormatter(formatter)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRAKTIKUMTOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGTOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHATID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения в telegram."""
    logger.info('Отправка сообщения')
    try:
        logger.info('Сообщение отправлено')
        return bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.TelegramError as err:
        error = f'Сбой в работе программы:{err}'
        logger.error(error)


def get_api_answer(current_timestamp):
    """Получаем ответ от API и приводим к формату Python."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        logger.info('Есть response')
        homework_dict = response.json()

        if type(homework_dict) is not dict:
            raise json.JSONDecodeError(
                'Не словарь'
            )
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        msg = f'Ошибка {error}'
        logging.error(msg)
    else:
        if response.status_code != HTTPStatus.OK:
            raise ValueError(
                'Статус кода не 200'
            )
        return homework_dict


def check_response(response):
    """Выбираем нужные данные от API."""
    if len(response) == 0:
        raise ValueError(
            'Длинна словаря равна 0'
        )
    if type(response) is not dict:
        raise TypeError(
            'Получили не словарь'
        )
    if 'homeworks' not in response:
        raise TypeError(
            'Not key homework'
        )

    try:
        homework = response.get('homeworks')
        if type(homework) is not list:
            raise TypeError(
                'not a list'
            )
        if len(homework) == 0:
            logger.error('Emptylist')

    except TypeError as err:
        error = f'Ошибка {err}'
        logger.error(error)
    else:
        return homework[0]


def parse_status(homework):
    """Проверка статуса работы."""
    if 'status' not in homework:
        raise KeyError(
            'Нет ключа status'
        )
    if 'homework_name' not in homework:
        raise KeyError(
            'Нет ключа homework_name'
        )
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
        return (
            f'Изменился статус проверки работы "{homework_name}". {verdict}'
        )
    else:
        raise TypeError(
            'Unknown status'
        )


def check_tokens():
    """Доступность переменных окружения."""
    TOKENS = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in TOKENS:
        try:
            if token is None:
                raise TypeError(
                    'token is None'
                )
            if type(token) is not str:
                raise TypeError(
                    'type token not str'
                )
        except TypeError as err:
            error = f'Нет переменной {token}, ошибка {err}'
            logger.critical(error)
            return False
        else:
            return True


def main():
    """Основная логика работы бота."""
    logger.info('Бот работает')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            current_timestamp = int(time.time())
            logger.info(current_timestamp)
            logger.info('Continue')
            if check_tokens():
                response = check_response(get_api_answer(current_timestamp))
                parse = parse_status(response)
                send_message(bot, parse)
                time.sleep(RETRY_TIME)
            else:
                raise ValueError

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            current_timestamp = int(time.time())
            logger.error(message)
            time.sleep(RETRY_TIME)
        else:
            current_timestamp = int(time.time())


if __name__ == '__main__':
    main()
