# Сторис: Артур — 1000 подписчиков

Праздничный слайд для Instagram Stories (1080×1920).

## Файлы

- `artur-1000.html` — исходник
- `artur-1000.png` / `artur-1000.jpg` — экспорт
- `assets/artur-volcano.jpg` — фон

## Композиция

1. Бренд **АРТУР** (крупно, serif)
2. Акцент **1 000** (лайм `#D9FF50`)
3. Подпись **ПОДПИСЧИКОВ**
4. Благодарность + CTA

## Пересборка

```bash
google-chrome --headless=new --no-sandbox --disable-gpu \
  --user-data-dir=/tmp/chrome-story-1000 \
  --hide-scrollbars --window-size=1080,1920 \
  --virtual-time-budget=4000 \
  --screenshot="$PWD/artur-1000.png" \
  "file://$PWD/artur-1000.html?static=1"
```
