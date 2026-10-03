# Сторис: Для кого это

Готовый слайд для Instagram Stories (1080×1920).

## Файлы для публикации

- `dlya-kogo.jpg` — удобнее для Stories
- `dlya-kogo.png` — максимальное качество

## Что на слайде

- **Композиция:** Артур справа (как девушка на B&W-референсе), текст слева/поверх с контролем читаемости
- **Фото:** cutout без фона, high-contrast B&W под стиль референса
- **Шрифты как у тарифа:** Oranienbaum (заголовок) + Montserrat (текст, ALL CAPS)
- **Структура как у тарифа «План»:** 3 карточки с лейблами на бордере + CTA
- **Палитра Coolors** `177ae3-9b3441-b355eb-ab6d78-25c5df` (акцент — cyan `#25C5DF`)

## Контент

1. Если вы узнаёте себя хотя бы в одном пункте
2. 6 пунктов (дубликат «Лишний вес…» убран)
3. Не «для идеальных». Для реальных людей с реальной физиологией

## Пересборка PNG

```bash
google-chrome --headless=new --no-sandbox --disable-gpu \
  --user-data-dir=/tmp/chrome-story \
  --hide-scrollbars --window-size=1080,1920 \
  --virtual-time-budget=5000 \
  --screenshot="$PWD/dlya-kogo.png" \
  "file://$PWD/dlya-kogo.html"
```
