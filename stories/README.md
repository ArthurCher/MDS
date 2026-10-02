# Сторис: тариф «План»

Готовый слайд для Instagram Stories (1080×1920).

## Файлы для публикации

- `tarif-plan.jpg` — удобнее для Stories
- `tarif-plan.png` — максимальное качество

## Что на слайде

- Фон: Артур (без текста на фото)
- Современные шрифты: Montserrat + Manrope
- Блоки: как стартуем / что входит / кому подойдёт
- Цена: 12 000 ₽ / месяц
- CTA: «Напиши в директ»

## Исходники

- `tarif-plan.html` — вёрстка
- `bg-artur-1080.jpg` — фон 1080×1920
- `fonts/` — локальные шрифты

## Пересборка PNG

```bash
google-chrome --headless=new --no-sandbox --disable-gpu \
  --user-data-dir=/tmp/chrome-story \
  --hide-scrollbars --window-size=1080,1920 \
  --virtual-time-budget=5000 \
  --screenshot="$PWD/tarif-plan.png" \
  "file://$PWD/tarif-plan.html"
```
