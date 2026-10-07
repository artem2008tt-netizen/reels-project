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
const wav = path.join("transcripts", `${name}.wav`);

// Whisper принимает только WAV 16 кГц моно
execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-i", input, "-vn", "-ar", "16000", "-ac", "1", wav]);

const whisperCppOutput = await transcribe({
  inputPath: wav,
  whisperPath: WHISPER_PATH,
  whisperCppVersion: WHISPER_VERSION,
  model: WHISPER_MODEL,
  language: "ru",
  tokenLevelTimestamps: true,
  splitOnWord: true,
});
fs.rmSync(wav);

const { captions } = toCaptions({ whisperCppOutput });
const text = captions.map((c) => c.text).join("").trim();

fs.writeFileSync(path.join("transcripts", `${name}.json`), JSON.stringify(captions, null, 2));
fs.writeFileSync(path.join("transcripts", `${name}.txt`), text + "\n");

const timed = captions.filter((c) => c.endMs > c.startMs).length;
const cyrillic = /[а-яё]/i.test(text);
console.log(`Слов: ${captions.length}, с таймингами: ${timed}, кириллица: ${cyrillic ? "да" : "нет"}`);
console.log(text.slice(0, 300));
