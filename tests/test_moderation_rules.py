"""
Unit tests for algorithmic moderation rules (_check_text_rules, _FLOOD_RE, _TEXT_BAN_RE).
No AI calls, no network, no Telegram bot needed.
"""
import re
import pytest

# ── Копируем логику из services/moderation.py чтобы не тащить зависимости ──
_TEXT_BAN_RE = re.compile(
    r"(https?://|t\.me/|@|\+?[78][\s\-]?\(?\d{3}\)?"
    r"[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})",
    re.IGNORECASE,
)
_FLOOD_RE = re.compile(r"(.)\1{5,}")


def _check_text_rules(text: str) -> tuple[bool, str]:
    if _TEXT_BAN_RE.search(text):
        return False, "Запрещены ссылки, теги (@...) и номера телефонов"
    if _FLOOD_RE.search(text):
        return False, "Текст содержит флуд"
    if len(text) > 500:
        return False, "Описание слишком длинное (максимум 500 символов)"
    return True, ""


# ── Helpers ──────────────────────────────────────────────────────────────────

def ok(text): return _check_text_rules(text)
def banned(text): return not _check_text_rules(text)[0]


# ═══════════════════════════════════════════════════════════════════════════
# LINKS
# ═══════════════════════════════════════════════════════════════════════════

class TestLinks:
    def test_http_url(self):
        assert banned("Купи аккаунт http://cheats.ru")

    def test_https_url(self):
        assert banned("https://vk.com/bs_sale")

    def test_tme_link(self):
        assert banned("Пиши t.me/mybsshop")

    def test_tme_link_with_at(self):
        assert banned("Перейди на t.me/+AbCdEfGhIj")

    def test_at_username(self):
        assert banned("Продаю акк, пиши @seller123")

    def test_at_in_middle(self):
        assert banned("Связь через @best_buyer")

    def test_at_no_username_space(self):
        # "@" alone with nothing after — should still trigger (@ is in pattern)
        assert banned("Напиши мне @ личку")

    def test_clean_text_no_link(self):
        r, _ = _check_text_rules("Ищу тиммейта на рейтинг, 30к кубков")
        assert r is True


# ═══════════════════════════════════════════════════════════════════════════
# PHONE NUMBERS
# ═══════════════════════════════════════════════════════════════════════════

class TestPhones:
    def test_ru_mobile_compact(self):
        assert banned("+79161234567")

    def test_ru_mobile_spaces(self):
        assert banned("+7 916 123 45 67")

    def test_ru_mobile_dashes(self):
        assert banned("8-916-123-45-67")

    def test_ru_mobile_parentheses(self):
        assert banned("8(916)123-45-67")

    def test_ru_mobile_7_prefix(self):
        assert banned("79161234567")

    def test_ru_mobile_mixed(self):
        assert banned("+7 (916) 123-45-67")

    def test_non_phone_digits(self):
        # Просто число без телефонного формата
        r, _ = _check_text_rules("У меня 30000 кубков и 15 легенд")
        assert r is True

    def test_cups_number_not_phone(self):
        r, _ = _check_text_rules("50000 кубков, топ 1 в регионе")
        assert r is True


# ═══════════════════════════════════════════════════════════════════════════
# FLOOD
# ═══════════════════════════════════════════════════════════════════════════

class TestFlood:
    def test_repeated_char_6(self):
        assert banned("аааааа")

    def test_repeated_char_10(self):
        assert banned("aaaaaaaaaa это флуд")

    def test_repeated_char_5_ok(self):
        # ровно 5 повторений — граница, должно проходить (паттерн {5,} = 6+)
        r, _ = _check_text_rules("aaaaa норм")
        assert r is True

    def test_repeated_digits_flood(self):
        assert banned("111111 кубков")

    def test_repeated_exclamation(self):
        assert banned("Топ!!!!!!")

    def test_normal_text_no_flood(self):
        r, _ = _check_text_rules("Ищу напарника в рейтинге. Есть дискорд.")
        assert r is True


# ═══════════════════════════════════════════════════════════════════════════
# LENGTH
# ═══════════════════════════════════════════════════════════════════════════

class TestLength:
    def test_exactly_500_ok(self):
        # Используем чередующиеся символы чтобы не триггерить flood-фильтр
        text = "аб" * 250  # 500 символов, нет флуда
        r, _ = _check_text_rules(text)
        assert r is True

    def test_501_rejected(self):
        text = "аб" * 250 + "в"  # 501 символ
        assert banned(text)

    def test_empty_not_rejected_by_rules(self):
        # Пустая строка — rules пропускают (moderate_text сам обрабатывает)
        r, _ = _check_text_rules("")
        assert r is True

    def test_long_text_with_link_caught_by_link_first(self):
        # Длинный текст с ссылкой — должен блокироваться по ссылке
        text = "а" * 600 + " https://evil.com"
        r, reason = _check_text_rules(text)
        assert r is False
        assert "ссылки" in reason


# ═══════════════════════════════════════════════════════════════════════════
# COMBINED / EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_link_and_phone_both_caught(self):
        assert banned("http://site.ru, звони +79001234567")

    def test_obfuscated_link_dot_me(self):
        # t.me обфускация через пробел — НЕ поймается паттерном (t . me)
        # Это известное ограничение regex-подхода — тест документирует поведение
        r, _ = _check_text_rules("пиши t . me / username")
        assert r is True  # regex не ловит — AI должен поймать

    def test_at_in_email_like_context(self):
        # @ — паттерн ловит любой @
        assert banned("мой email: user@mail.ru")

    def test_unicode_flood(self):
        assert banned("🔥🔥🔥🔥🔥🔥 продам")

    def test_normal_game_description(self):
        r, _ = _check_text_rules(
            "Привет! Ищу тиммейта на рейтинговые бои. "
            "Играю за стрелков и поддержку. 25к кубков, тир Диамант."
        )
        assert r is True

    def test_sale_text_no_link_passes_rules(self):
        # Без ссылки/телефона/флуда — regex не заблокирует, AI должен поймать
        r, _ = _check_text_rules("Продаю аккаунт, дёшево, без доната")
        assert r is True  # regex пропускает — это работа AI

    def test_http_case_insensitive(self):
        assert banned("HTTP://SITE.COM")

    def test_tme_uppercase(self):
        assert banned("T.ME/channel")
