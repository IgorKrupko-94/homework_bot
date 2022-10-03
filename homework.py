import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from homework_bot.exceptions import UnavailabilityEndpoint, \
    RequestFailureEndpoint, ErrorValueDictionary, VariablesNotDefined

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    filename='homework.log',
    filemode='w'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляем сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(
            f'В чат успешно отправлено сообщение {message}.'
        )
    except telegram.TelegramError:
        logger.exception('Сбой при отправке сообщения в Telegram')


def get_api_answer(current_timestamp: int) -> dict:
    """Делаем запрос к единственному эндпоинту API-сервиса
    Практикум.Домашка.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        if response.status_code != HTTPStatus.OK:
            message_error = (
                f'Эндпоинт недоступен. '
                f'Статус-код ответа API: {response.status_code}'
            )
            logger.error(message_error)
            raise UnavailabilityEndpoint(message_error)
        return response.json()
    except Exception as error:
        logger.error(error, exc_info=True)
        raise RequestFailureEndpoint(
            f'Сбой при запросе к эндпоинту: {error}'
        )


def check_response(response: dict) -> list:
    """Проверяем ответ API на корректность."""
    if response['homeworks'] is None:
        message_error = 'Ошибка получения значения по ключу в словаре'
        logger.error(message_error)
        raise ErrorValueDictionary(message_error)
    homeworks = response['homeworks']
    return homeworks


def parse_status(homework: dict) -> str:
    """Извлекаем из информации о конкретной домашней работе
    статус этой работы.
    """
    if homework['homework_name'] is None:
        message_error = 'Ошибка получения значения по ключу в словаре'
        logger.error(message_error)
        raise ErrorValueDictionary(message_error)
    homework_name = homework['homework_name']
    if homework['status'] is None:
        message_error = 'Ошибка получения значения по ключу в словаре'
        logger.error(message_error)
        raise ErrorValueDictionary(message_error)
    homework_status = homework['status']
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError as error:
        logger.error(error, exc_info=True)
        raise ErrorValueDictionary(
            f'Недокументированный статус домашней работы: {error}'
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяем доступность переменных окружения."""
    variables = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    for name, variable in variables.items():
        if variable is None:
            logger.critical(
                f'Отсутствует обязательная переменная окружения - {name}.'
            )
            return False
    return True


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        raise VariablesNotDefined(
            'Не заданы обязательные переменные окружения'
        )
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    previous_time = ''
    message_error = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                if homework['date_updated'] != previous_time:
                    previous_time = homework['date_updated']
                    message = parse_status(homework)
                    send_message(bot, message)
                else:
                    logger.debug('Новых статусов не обнаружено')
            current_timestamp = response.get('current_date')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != message_error:
                send_message(bot, message)
                message_error = message
            time.sleep(RETRY_TIME)

        else:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
