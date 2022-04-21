import time
import telegram
from dotenv import load_dotenv
import logging
import os
import requests

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    filename='homework.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

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
    logging.info('Отправка сообщения')
    try:
        logging.info('Сообщение отправлено')
        return bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as err:
        error = f'Сбой в работе программы:{err}'
        logging.error(error)


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
        if not response:
            raise ValueError(
                'Нет response'
            )
        else:
            logging.debug('Есть response')
        if type(response.json()) is not dict:
            raise TypeError(
                'Не словарь'
            )
    except (ValueError, TypeError) as error:
        msg = f'Ошибка {error}'
        logging.error(msg)
    else:
        if response.status_code != 200:
            raise ValueError(
                'Статус кода не 200'
            )
        homework_dict = response.json()
        return homework_dict


def check_response(response):
    """Выбираем нужные данные от API."""
    if len(response) == 0:
        raise ValueError(
            'Пустой словарь'
        )
    if type(response) != dict:
        raise TypeError(
            'Получили не словарь'
        )
    if 'homeworks' not in response:
        raise ValueError(
            'Not key homework'
        )

    try:
        homeworks = response.get('homeworks')
        if type(homeworks) != list:
            raise TypeError(
                'not a list'
            )
    except (ValueError, TypeError) as err:
        error = f'Ошибка {err}'
        logging.error(error)
    else:
        homeworks = response.get('homeworks')
        return homeworks


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
    try:
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')
    except Exception as err:
        error = f'Error {err}'
        logging.error(error)
    else:
        if homework_status in HOMEWORK_STATUSES:
            verdict = HOMEWORK_STATUSES[homework_status]
            return f'Изменился статус проверки работы "' \
                   f'{homework_name}". {verdict}'
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
            if type(token) != str:
                raise TypeError(
                    'type token not str'
                )
        except TypeError as err:
            error = f'Нет переменной {token}, ошибка {err}'
            logging.critical(error)
            return False
        else:
            return True


def main():
    """Основная логика работы бота."""
    logging.info('Бот работает')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            check_tokens()
            response = check_response(get_api_answer(current_timestamp))
            parse = parse_status(response)
            send_message(bot, parse)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            time.sleep(RETRY_TIME)
        else:
            current_timestamp = int(time.time())


if __name__ == '__main__':
    main()
