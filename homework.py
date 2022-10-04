import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (UnavailabilityEndpoint,
                        RequestFailureEndpoint,
                        ErrorValueDictionary,
                        ObjectNotInstance,
                        SendMessageTelegramError
                        )

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
        logger.debug(
            f'Начинаем отправлять сообщение {message}'
        )
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.TelegramError:
        raise SendMessageTelegramError(
            f'Ошибка при отправке сообщения {message} в Telegram чат'
        )
    else:
        logger.info(
            f'В чат успешно отправлено сообщение {message}.'
        )


def get_api_answer(current_timestamp: int) -> dict:
    """Делаем запрос к эндпоинту API-сервиса Практикум.Домашка."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        if response.status_code != HTTPStatus.OK:
            raise UnavailabilityEndpoint(
                f'Эндпоинт недоступен. '
                f'Статус-код ответа API: {response.status_code}'
            )
        return response.json()
    except Exception as error:
        raise RequestFailureEndpoint(
            f'Сбой при запросе к эндпоинту: {error}'
        )


def check_response(response: dict) -> list:
    """Проверяем ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Переданный объект не является словарём')
    homeworks = response.get('homeworks')
    if homeworks is None:
        raise KeyError(
            'Ошибка получения значения по ключу в словаре'
        )
    if not isinstance(homeworks, list):
        raise ObjectNotInstance(
            'Полученный объект не является списком'
        )
    return homeworks


def parse_status(homework: dict) -> str:
    """Извлекаем из информации о домашней работе статус этой работы."""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyError(
            'Ошибка получения значения по ключу в словаре'
        )
    homework_status = homework.get('status')
    if homework_status is None:
        raise KeyError(
            'Ошибка получения значения по ключу в словаре'
        )
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError as error:
        raise ErrorValueDictionary(
            f'Недокументированный статус домашней работы: {error}'
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяем доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        message_error = 'Не заданы обязательные переменные окружения'
        logger.critical(message_error)
        sys.exit(message_error)
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

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
