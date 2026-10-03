# Сторис: Для кого это

Готовый слайд для Instagram Stories (1080×1920).

## Стиль

- Как референс с девушкой: левая колонка текста + крупный герой справа
- Чистый текст на светлом фоне — **без плашек, рамок, обводок**
- Артур: правая половина, во всю высоту (по пояс / грудь)
- Текст: крупный, равномерно по высоте левой колонки (~48% ширины)
- От тарифа «План»: только Oranienbaum + Montserrat и размеры

## Пересборка

```bash
google-chrome --headless=new --no-sandbox --disable-gpu \
  --user-data-dir=/tmp/chrome-story \
  --hide-scrollbars --window-size=1080,1920 \
  --virtual-time-budget=5000 \
  --screenshot="$PWD/dlya-kogo.png" \
  "file://$PWD/dlya-kogo.html"
```
