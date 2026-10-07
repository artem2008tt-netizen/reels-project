// Расшифровка речи на русском: node scripts/transcribe.mjs public/video.mp4
// Результат: transcripts/<имя>.txt (текст на проверку) и transcripts/<имя>.json (слова с таймингами)
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { toCaptions, transcribe } from "@remotion/install-whisper-cpp";
import { WHISPER_MODEL, WHISPER_PATH, WHISPER_VERSION } from "./whisper-config.mjs";

const input = process.argv[2];
if (!input || !fs.existsSync(input)) {
  console.error("Файл не найден:", input);
  process.exit(1);
}

const name = path.parse(input).name;
fs.mkdirSync("transcripts", { recursive: true });
const wav = path.resolve("transcripts", `${name}.wav`); // whisper запускается из своей папки — нужен полный путь

// Whisper принимает только WAV 16 кГц моно
execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-i", input, "-vn", "-ar", "16000", "-ac", "1", wav]);

const whisperCppOutput = await transcribe({
  inputPath: wav,
  whisperPath: WHISPER_PATH,
  whisperCppVersion: WHISPER_VERSION,
  model: WHISPER_MODEL,
  language: "ru",
  tokenLevelTimestamps: true,
});
fs.rmSync(wav);

const { captions: tokens } = toCaptions({ whisperCppOutput });

// Whisper отдаёт кусочки слов («Р», «ед», «ак»); новое слово начинается с пробела — склеиваем в слова
const captions = [];
for (const t of tokens) {
  const last = captions[captions.length - 1];
  if (!last || t.text.startsWith(" ")) {
    captions.push({ ...t });
  } else {
    last.text += t.text;
    last.endMs = t.endMs;
    last.confidence = Math.min(last.confidence ?? 1, t.confidence ?? 1);
  }
}
const text = captions.map((c) => c.text).join("").trim();

fs.writeFileSync(path.join("transcripts", `${name}.json`), JSON.stringify(captions, null, 2));
fs.writeFileSync(path.join("transcripts", `${name}.txt`), text + "\n");

const timed = captions.filter((c) => c.endMs > c.startMs).length;
const cyrillic = /[а-яё]/i.test(text);
console.log(`Слов: ${captions.length}, с таймингами: ${timed}, кириллица: ${cyrillic ? "да" : "нет"}`);
console.log(text.slice(0, 300));
