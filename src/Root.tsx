import "./index.css";
import { Composition } from "remotion";
import { Test } from "./Test";

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
    </>
  );
};
