class UnavailabilityEndpoint(Exception):
    """Статус-код ответа API не 200."""

    pass


class RequestFailureEndpoint(Exception):
    """Сбой при запросе к эндпоинту."""

    pass


class ErrorValueDictionary(Exception):
    """Ошибка получения значения по ключу в словаре."""

    pass


class VariablesNotDefined(Exception):
    """Отсутствуют обязательные переменные окружения."""

    pass
