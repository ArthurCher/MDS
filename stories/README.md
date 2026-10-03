# Сторис: тарифы «План» и «Контроль»

Слайды для Instagram Stories (1080×1920). Структура: шапка → 3 блока → CTA.

## Скачать

### Тариф «План» — 12 000 ₽
- `tarif-plan.jpg` / `tarif-plan.png`
- `../Тариф-План-сторис-NEW.jpg` / `.png`

### Тариф «Контроль» — 20 000 ₽
- `tarif-kontrol.jpg` / `tarif-kontrol.png`
- `../Тариф-Контроль-сторис.jpg` / `.png`

## Акценты (лайм `#D9FF50`)

- бейдж **онлайн**
- слово **директ** в CTA
- круглые маркеры и чекбоксы

## Фон

- Оба слайда: `bg-artur-studio.jpg` + одинаковое затемнение
- Силуэт Артура читается, текст контрастный

## Исходники

- `tarif-plan.html`
- `tarif-kontrol.html`
- `fonts/` — Montserrat + Oranienbaum

## Пересборка

```bash
google-chrome --headless=new --no-sandbox --disable-gpu \
  --user-data-dir=/tmp/chrome-story \
  --hide-scrollbars --window-size=1080,1920 \
  --virtual-time-budget=5000 \
  --screenshot="$PWD/tarif-kontrol.png" \
  "file://$PWD/tarif-kontrol.html"
```
