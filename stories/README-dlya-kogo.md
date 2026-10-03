# Сторис: Для кого это

Готовый слайд для Instagram Stories (1080×1920).

## Файлы для публикации

- `dlya-kogo.jpg` — удобнее для Stories
- `dlya-kogo.png` — максимальное качество

## Стиль

- **Как референс с девушкой:** светлый студийный B&W, текст прозрачно поверх фото, вертикальный стек CAPS + тонкие разделители
- **Без рамок / карточек / табличных плашек**
- **От тарифа «План»:** только шрифты и размеры — Oranienbaum (заголовок 82px, секции 34px) + Montserrat
- **Артур:** cutout B&W справа, корпус; текст читается поверх

## Пересборка PNG

```bash
google-chrome --headless=new --no-sandbox --disable-gpu \
  --user-data-dir=/tmp/chrome-story \
  --hide-scrollbars --window-size=1080,1920 \
  --virtual-time-budget=5000 \
  --screenshot="$PWD/dlya-kogo.png" \
  "file://$PWD/dlya-kogo.html"
```
