# YourSEOAgent — WordPress-тема

Порт статического сайта [yourseoagent.pro](https://yourseoagent.pro/) в WordPress-тему.

## Установка

1. Скопируйте папку `yourseoagent` в `wp-content/themes/` на хостинге (или загрузите ZIP через **Внешний вид → Темы → Добавить**).
2. Активируйте тему **YourSEOAgent**.
3. Откройте **Настройки → Постоянные ссылки** и выберите «Название записи» (или любую ЧПУ-структуру), затем сохраните.
4. При активации тема сама создаёт страницы и назначает шаблоны.

## Страницы и URL

| Страница | URL |
|---|---|
| Главная | `/` |
| AI-агент | `/services/ai-agent/` |
| Betting/Gaming | `/services/betting-gaming/` |
| Технический аудит | `/services/tehnicheskiy-audit/` |
| GEO/AISEO | `/services/geo-aiseo/` |
| СНГ/Яндекс | `/services/sng-yandex/` |
| Контакты | `/contacts/` |

Контент зафиксирован в page templates — визуально совпадает с исходными HTML.

## SEO

- Meta description задаётся через `_ysa_meta_description`.
- `robots.txt` — стандартный WordPress + строка `Sitemap`.
- `/sitemap.xml` редиректит на `/wp-sitemap.xml` (WP 5.5+) или отдаёт упрощённый sitemap.

## Контакты в теме

Константы в `functions.php`: Telegram, WhatsApp, телефон, email.
