// Ставит whisper.cpp и русскоязычную модель в папку whisper.cpp/
import { installWhisperCpp, downloadWhisperModel } from "@remotion/install-whisper-cpp";
import { WHISPER_MODEL, WHISPER_PATH, WHISPER_VERSION } from "./whisper-config.mjs";

await installWhisperCpp({ to: WHISPER_PATH, version: WHISPER_VERSION });
await downloadWhisperModel({ model: WHISPER_MODEL, folder: WHISPER_PATH });
console.log("Whisper готов:", WHISPER_PATH, WHISPER_MODEL);
