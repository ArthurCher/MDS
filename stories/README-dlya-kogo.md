# Сторис: Для кого это

Готовый слайд для Instagram Stories (1080×1920).

## Файлы для публикации

- `dlya-kogo.jpg` — удобнее для Stories
- `dlya-kogo.png` — максимальное качество

## Что на слайде

- Фон: Артур (cutout без фона, цветокор под палитру)
- Шрифты как у тарифа: Oranienbaum + Montserrat
- Структура блоков как у тарифа «План»: 3 карточки + CTA
- Акцент: `#25C5DF` / `#177AE3` / `#B355EB` (Coolors `177ae3-9b3441-b355eb-ab6d78-25c5df`)

## Пересборка PNG

```bash
google-chrome --headless=new --no-sandbox --disable-gpu \
  --user-data-dir=/tmp/chrome-story \
  --hide-scrollbars --window-size=1080,1920 \
  --virtual-time-budget=5000 \
  --screenshot="$PWD/dlya-kogo.png" \
  "file://$PWD/dlya-kogo.html"
```
