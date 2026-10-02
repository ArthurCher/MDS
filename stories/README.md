# Сторис: тариф «План»

Готовый слайд для Instagram Stories (1080×1920).

## Файлы для публикации

- `tarif-plan.png` — PNG, максимальное качество
- `tarif-plan.jpg` — JPG, удобнее для загрузки в Stories

## Исходники

- `tarif-plan.html` — вёрстка слайда (можно править текст и экспортнуть заново)
- `bg-story-plan.jpg` — фон
- `fonts/` — локальные шрифты Cormorant Garamond + Manrope

## Как пересобрать PNG

```bash
google-chrome --headless=new --no-sandbox --disable-gpu \
  --user-data-dir=/tmp/chrome-story \
  --hide-scrollbars --window-size=1080,1920 \
  --virtual-time-budget=5000 \
  --screenshot="$PWD/tarif-plan.png" \
  "file://$PWD/tarif-plan.html"
```
