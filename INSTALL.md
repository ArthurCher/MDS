# Как развернуть YourSEOAgent на сервере

Тема для WordPress — порт сайта [yourseoagent.pro](https://yourseoagent.pro/).

## Скачать архив темы

**Прямая ссылка (ZIP темы):**  
https://github.com/ArthurCher/MDS/raw/cursor/wordpress-theme-yourseoagent-9e3b/dist/yourseoagent-theme.zip

Альтернатива — ZIP всей ветки:  
https://github.com/ArthurCher/MDS/archive/refs/heads/cursor/wordpress-theme-yourseoagent-9e3b.zip  
(тогда тема лежит внутри: `…/wp-content/themes/yourseoagent/`)

---

## Вариант A. WordPress уже установлен (рекомендуется)

### 1. Загрузить тему
1. Войдите в админку: `https://ваш-домен/wp-admin/`
2. **Внешний вид → Темы → Добавить → Загрузить тему**
3. Выберите файл `yourseoagent-theme.zip`
4. Нажмите **Установить**, затем **Активировать**

Через FTP/SSH: распакуйте ZIP так, чтобы получилось  
`wp-content/themes/yourseoagent/` (внутри `style.css`, `functions.php` и т.д.).

### 2. Включить ЧПУ
1. **Настройки → Постоянные ссылки**
2. Выберите **«Название записи»** (`/%postname%/`)
3. **Сохранить изменения**

Без этого URL вида `/services/ai-agent/` могут не открываться.

### 3. Проверить страницы
После активации тема сама создаёт страницы. Откройте:

| Страница | URL |
|---|---|
| Главная | `/` |
| AI-агент | `/services/ai-agent/` |
| Betting/Gaming | `/services/betting-gaming/` |
| Технический аудит | `/services/tehnicheskiy-audit/` |
| GEO/AISEO | `/services/geo-aiseo/` |
| СНГ/Яндекс | `/services/sng-yandex/` |
| Контакты | `/contacts/` |

Если главная не та: **Настройки → Чтение → «Главная страница»** → страница **Главная**.

### 4. Домен и SSL
- Привяжите домен к хостингу (A-запись / Cloudflare).
- Включите HTTPS (Let’s Encrypt в панели или плагин/хостинг).
- **Настройки → Общие**: `Адрес WordPress` и `Адрес сайта` = `https://ваш-домен` (без `/` в конце).

Готово: сайт должен выглядеть как yourseoagent.pro.

---

## Вариант B. Чистый сервер (нет WordPress)

### Требования
- PHP 7.4+ (лучше 8.1/8.2)
- MySQL 5.7+ / MariaDB 10.3+
- Apache + `mod_rewrite` **или** Nginx

### Краткие шаги
1. Установите WordPress (панель хостинга «1 клик» или [wordpress.org/download](https://wordpress.org/download/)).
2. Создайте БД и пользователя MySQL, пройдите мастер установки WP.
3. Дальше — **Вариант A** (загрузка ZIP темы).

### Apache
В корне сайта должен быть `.htaccess` от WordPress (появляется после сохранения постоянных ссылок). Нужен `AllowOverride All`.

### Nginx (фрагмент)
```nginx
location / {
    try_files $uri $uri/ /index.php?$args;
}
```

---

## Миграция со статического HTML

Если сейчас на домене лежат `index.html` и папка `services/`:

1. Сделайте бэкап старых файлов.
2. Установите WordPress в корень домена (или в подпапку, потом перенесёте).
3. Активируйте тему YourSEOAgent.
4. Настройте редиректы со старых URL (если нужны `.html`):

| Было | Стало |
|---|---|
| `/index.html` | `/` |
| `/contacts.html` | `/contacts/` |
| `/services/ai-agent.html` | `/services/ai-agent/` |
| `/services/betting-gaming.html` | `/services/betting-gaming/` |
| `/services/tehnicheskiy-audit.html` | `/services/tehnicheskiy-audit/` |
| `/services/geo-aiseo.html` | `/services/geo-aiseo/` |
| `/services/sng-yandex.html` | `/services/sng-yandex/` |

Пример для `.htaccess` (Apache):
```apache
Redirect 301 /index.html /
Redirect 301 /contacts.html /contacts/
Redirect 301 /services/ai-agent.html /services/ai-agent/
Redirect 301 /services/betting-gaming.html /services/betting-gaming/
Redirect 301 /services/tehnicheskiy-audit.html /services/tehnicheskiy-audit/
Redirect 301 /services/geo-aiseo.html /services/geo-aiseo/
Redirect 301 /services/sng-yandex.html /services/sng-yandex/
```

---

## Частые проблемы

**Тема не появляется в списке**  
В ZIP должна быть папка `yourseoagent/` с `style.css` внутри. Не кладите файлы темы прямо в `themes/` без этой папки.

**404 на /services/…**  
Сохраните постоянные ссылки ещё раз. На Nginx проверьте `try_files`.

**Главная пустая / не та**  
Настройки → Чтение → статическая главная = «Главная».

**Стили «ломаются»**  
Очистите кеш плагина/CDN. Тема подключает Google Fonts — нужен исходящий доступ к `fonts.googleapis.com`.

---

## Контакты в теме

Правьте константы в `wp-content/themes/yourseoagent/functions.php`:
- `YSA_TELEGRAM_URL`
- `YSA_WHATSAPP_URL`
- `YSA_PHONE` / `YSA_PHONE_DISPLAY`
- `YSA_EMAIL`
