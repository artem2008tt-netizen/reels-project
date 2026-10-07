import "./index.css";
import { Composition } from "remotion";
import { Test } from "./Test";
import { FPS, OUTRO_FRAMES, Reels01, VIDEO_FRAMES } from "./Reels01";

// Формат по умолчанию: вертикальный 1080×1920, 30 кадров в секунду
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Test"
        component={Test}
        durationInFrames={150}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="Reels01"
        component={Reels01}
        durationInFrames={VIDEO_FRAMES + OUTRO_FRAMES}
        fps={FPS}
        width={1080}
        height={1920}
      />
    </>
  );
};
