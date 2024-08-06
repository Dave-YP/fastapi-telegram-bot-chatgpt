# status_codes.py

class StatusMessages:
    LOGIN_REQUIRED = "Пожалуйста, войдите с помощью команды /login."
    SESSION_EXPIRED = "Ваша сессия истекла. Пожалуйста, войдите снова с помощью команды /login."
    VALIDATION_ERROR = "Ошибка 422: Неверный запрос. Пожалуйста, попробуйте снова или обратитесь в поддержку."
    MESSAGE_LIMIT_REACHED = "Ошибка 451: Достигнут дневной лимит сообщений."
    FORBIDDEN = "Ошибка 403: Запрещено. Ваш регион не поддерживается."
    SERVER_ERROR = "Ошибка 500: Внутренняя ошибка сервера. Пожалуйста, попробуйте позже."
    UNEXPECTED_ERROR = "Неожиданная ошибка: HTTP {status}"
    UNAUTHORIZED = "Unauthorized"

    @staticmethod
    def get_message_limit_text(limit):
        if limit % 10 == 1 and limit % 100 != 11:
            return f"Ошибка 451: Достигнут дневной лимит в {limit} вопрос."
        elif limit % 10 in [2, 3, 4] and not (limit % 100 in [12, 13, 14]):
            return f"Ошибка 451: Достигнут дневной лимит в {limit} вопроса."
        else:
            return f"Ошибка 451: Достигнут дневной лимит в {limit} вопросов."
