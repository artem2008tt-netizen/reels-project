import {
  AbsoluteFill,
  interpolate,
  OffthreadVideo,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export const NICK = "@nat.mol4anova";
export const FPS = 30;
export const VIDEO_FRAMES = Math.round(37.1 * FPS); // длина исходника reels_01.mp4
export const OUTRO_FRAMES = 4 * FPS; // финальный экран — 4 секунды

const BRAND = { navy: "#05070F", blue: "#2E8BFF", glow: "#9EC7FF" };

// Ник поверх видео: слева внизу, выше нижней безопасной зоны (400 px) и далеко от кнопок справа
const NickBadge: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div
      style={{
        position: "absolute",
        left: 60,
        bottom: 440,
        opacity,
        padding: "14px 28px",
        borderRadius: 999,
        background: "rgba(5, 7, 15, 0.72)",
        border: `2px solid ${BRAND.blue}`,
        boxShadow: `0 0 24px ${BRAND.blue}66`,
        color: "#fff",
        fontFamily: "Inter, Arial, sans-serif",
        fontWeight: 700,
        fontSize: 44,
      }}
    >
      {NICK}
    </div>
  );
};

// Финальный экран: только ник на тёмном фоне со свечением
const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 200 } });
  const opacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const drift = interpolate(frame, [0, OUTRO_FRAMES], [1, 1.04]); // лёгкое движение, кадр не стоит
  const pulse = 0.55 + 0.15 * Math.sin((frame / fps) * Math.PI);

  return (
    <AbsoluteFill style={{ background: BRAND.navy, alignItems: "center", justifyContent: "center" }}>
      <div
        style={{
          position: "absolute",
          width: 900,
          height: 900,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${BRAND.blue}55 0%, transparent 65%)`,
          opacity: pulse * opacity,
          transform: `scale(${drift})`,
        }}
      />
      <div
        style={{
          opacity,
          transform: `translateY(${interpolate(enter, [0, 1], [40, 0])}px) scale(${drift})`,
          color: "#fff",
          fontFamily: "Inter, Arial, sans-serif",
          fontWeight: 800,
          fontSize: 92,
          textShadow: `0 0 30px ${BRAND.blue}, 0 0 60px ${BRAND.glow}55`,
        }}
      >
        {NICK}
      </div>
    </AbsoluteFill>
  );
};

export const Reels01: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: BRAND.navy }}>
      <Sequence durationInFrames={VIDEO_FRAMES}>
        {/* исходник моно: при переводе в стерео каждый канал тише на 3 дБ — возвращаем громкость */}
        <OffthreadVideo src={staticFile("reels_01.mp4")} volume={Math.SQRT2} />
        <NickBadge />
      </Sequence>
      <Sequence from={VIDEO_FRAMES} durationInFrames={OUTRO_FRAMES}>
        <Outro />
      </Sequence>
    </AbsoluteFill>
  );
};
