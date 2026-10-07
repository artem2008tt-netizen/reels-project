import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// Тестовый ролик: светлый фон, по центру плавно появляется надпись
export const Test: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame, [0, fps], [0, 1], { extrapolateRight: "clamp" });
  const lift = spring({ frame, fps, config: { damping: 200 } });

  return (
    <AbsoluteFill className="items-center justify-center bg-slate-50">
      <h1
        className="text-[110px] font-bold text-slate-900"
        style={{
          fontFamily: "Inter, Arial, sans-serif",
          opacity,
          transform: `translateY(${interpolate(lift, [0, 1], [40, 0])}px)`,
        }}
      >
        Всё работает
      </h1>
    </AbsoluteFill>
  );
};
