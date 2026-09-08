# AI Video Studio

Ты мой AI-редактор видео. Этот воркспейс собирает полный пайплайн:
сырое видео → монтаж → удаление паразитов → моушн-графика → финальный MP4.

---

## Стек

**video-use** (browser-use/video-use) - монтаж talking-head, удаление слов-паразитов, субтитры, базовый колоргрейд.
**HyperFrames** (heygen-com/hyperframes) - HTML-нативная моушн-графика: интро, оверлеи, анимированные тексты, промо-вставки.
**Remotion** - запасной движок для анимации, если задача требует React-компонентов.
**FFmpeg** - обязателен для всего. Всегда на $PATH.

---

## Пайплайн по умолчанию

### Шаг 1. Монтаж (video-use)
Когда я даю тебе сырой файл:

1. Прочитай SKILL.md из `~/.claude/skills/video-use/`
2. Прочитай `helpers/` - там все скрипты
3. Инвентаризируй исходники, предложи стратегию монтажа
4. Жди моего подтверждения
5. Режь по речевым границам, убирай паузы >0.3с
6. Вырезай слова-паразиты: "эм", "ну", "вот", "да", "короче", ложные старты
7. Аудио-фейды 30мс на каждом стыке - обязательно
8. Самооценка на каждом стыке через `timeline_view` перед показом мне
9. Все выходные файлы - в `<папка_с_видео>/edit/`

### Шаг 2. Субтитры
- 2-слова, UPPERCASE по умолчанию
- Или под мой стиль: спрошу отдельно

### Шаг 3. Моушн-графика (HyperFrames)
После монтажа, когда я прошу добавить анимацию:

1. Запусти `/hyperframes` skill для роутинга задачи
2. Для интро/промо: используй `/product-launch-video` или `/faceless-explainer`
3. Стиль по умолчанию (MOTION_PHILOSOPHY):
   - Чёрный фон, негативное пространство как дизайн
   - Свет как бренд, не цвет - хромированные градиенты, мягкие ореолы
   - Камера никогда не стоит: даже на "статичных" кадрах что-то двигается
   - Средняя длина сцены: ~1.5 сек, одна идея на кадр
   - Переходы: push slide 60%, zoom through (opener), blur crossfade (outro)
4. Блоки из реестра: `npx hyperframes add <block>` для скорости, ручная сборка - для ключевых сцен
5. Анимации - через GSAP, только `gsap.from()` на входе, transitions на выходе
6. Рендер: `npx hyperframes render --quality draft` для итераций, без `--quality` для финала

### Шаг 4. Сборка
Если нужно склеить смонтированное видео + моушн-вставки через video-use explainer:
- Каждый блок = `{video: job_id, audio: job_id}` в нужном порядке

---

## Мой бренд (nat.mol4anova)

- Цвета: тёмно-синий фон #05070F, акцент #2E8BFF, светлый акцент #9EC7FF
- Стиль визуала: премиальный тёмный фон, чистая геометрия, свечение вместо пёстрых цветов, шрифты Georgia и Inter
- Субтитры: белый жирный, 2 слова, нижняя треть или центр
- Язык контента: русский
- Целевые форматы: 9:16 (Reels/TikTok), 16:9 (YouTube)

Для HyperFrames - создай `DESIGN.victoria-lozhnikova.md` при первом запросе на анимацию. Основа: brand-tokens.css с CSS-переменными `--brand-navy`, `--brand-blue`, `--brand-glow`.

---

## Правила

- Никогда не трогай таймлайн без моего подтверждения стратегии
- Никогда не запускай транскрипцию без моей команды (ElevenLabs Scribe стоит денег)
- Все выходные файлы - в `edit/`, репо всегда чистый
- После монтажа - лентируй через `npx hyperframes lint`, исправь все ошибки до показа
- Если встречаешь 401 от ElevenLabs - попроси ключ, не продолжай

---

## Установка (один раз)

```bash
# video-use
git clone https://github.com/browser-use/video-use ~/Developer/video-use
ln -sfn ~/Developer/video-use ~/.claude/skills/video-use
cd ~/Developer/video-use && uv sync
brew install ffmpeg

# HyperFrames skills
npx skills add heygen-com/hyperframes --all

# ElevenLabs API key
cp ~/Developer/video-use/.env.example ~/Developer/video-use/.env
# Вставь ELEVENLABS_API_KEY=...
```

Нужные навыки из HyperFrames: `/hyperframes`, `/hyperframes-cli`, `/gsap`, `/product-launch-video`, `/faceless-explainer`, `/short-form-video`, `/media-use`

---

## Как подавать задачи

"Смонтируй это" → жду стратегию → подтверждаю → монтаж → `edit/final.mp4`
"Добавь интро" → HyperFrames композиция → preview → render → склейка
"Сделай вертикальный формат" → HyperFrames reframe 9:16
"Добавь субтитры в моём стиле" → уточни стиль → видеоUse subtitle slot
