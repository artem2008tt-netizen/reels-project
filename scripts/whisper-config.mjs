import path from "node:path";

export const WHISPER_PATH = path.join(process.cwd(), "whisper.cpp");
export const WHISPER_VERSION = "1.5.5";
export const WHISPER_MODEL = "medium"; // многоязычная модель (без .en), понимает русский
