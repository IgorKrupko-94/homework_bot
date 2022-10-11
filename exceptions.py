class UnavailabilityEndpoint(Exception):
    """Статус-код ответа API не 200."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'UnavailabilityEndpoint, {self.message}'
        else:
            return 'UnavailabilityEndpoint, статус-код ответа не равен 200'


class RequestFailureEndpoint(Exception):
    """Сбой при запросе к эндпоинту."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'RequestFailureEndpoint, {self.message}'
        else:
            return 'RequestFailureEndpoint, ошибка при запросе к эндпоинту'


class ErrorValueDictionary(Exception):
    """Ошибка получения значения по ключу в словаре."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'ErrorValueDictionary, {self.message}'
        else:
            return ('ErrorValueDictionary,'
                    'получен недокументированный статус домашней работы')


class ObjectNotInstance(Exception):
    """Получаемый объект другого типа данных."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'ObjectNotInstance, {self.message}'
        else:
            return ('ObjectNotInstance, '
                    'полученный объект является неправильным типом данных')


class SendMessageTelegramError(Exception):
    """Ошибка при отправке сообщения в Telegram чат."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'SendMessageTelegramError, {self.message}'
        else:
            return ('SendMessageTelegramError, '
                    'ошибка при отправке сообщения в телеграм-чат')
