interface SkeletonProps {
  w?: string;
  h?: string;
  rounded?: string;
}

export function Skeleton({ w = "100%", h = "20px", rounded = "8px" }: SkeletonProps) {
  return (
    <div
      style={{ width: w, height: h, borderRadius: rounded }}
      className="shimmer bg-white/6"
    />
  );
}

export function SkeletonAlertCard() {
  return (
    <div className="echo-alert space-y-4">
      <div className="flex justify-between">
        <div className="space-y-2">
          <Skeleton w="120px" h="24px" rounded="999px" />
          <Skeleton w="200px" h="28px" />
          <Skeleton w="140px" h="16px" />
        </div>
        <Skeleton w="80px" h="56px" />
      </div>
      <Skeleton w="100%" h="6px" rounded="999px" />
      <div className="rounded-xl border border-white/8 bg-white/4 p-4 space-y-3">
        <Skeleton w="100%" h="40px" />
        <Skeleton w="100%" h="40px" />
        <Skeleton w="80%" h="40px" />
      </div>
    </div>
  );
}

export function SkeletonGauge() {
  return (
    <div className="flex flex-col items-center gap-3">
      <Skeleton w="80px" h="80px" rounded="50%" />
      <Skeleton w="60px" h="12px" />
    </div>
  );
}

export function SkeletonIncident() {
  return (
    <div className="flex gap-4 items-start rounded-xl border border-white/8 bg-white/4 p-4">
      <Skeleton w="32px" h="32px" rounded="8px" />
      <div className="flex-1 space-y-2">
        <Skeleton w="70%" h="16px" />
        <Skeleton w="40%" h="12px" />
      </div>
    </div>
  );
}

export function SkeletonDemoSection() {
  return (
    <div className="grid md:grid-cols-[1fr_auto_1fr] gap-4 max-w-5xl mx-auto">
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6 space-y-4">
        <Skeleton w="50%" h="14px" />
        <Skeleton w="90%" h="22px" />
        <Skeleton w="60%" h="14px" />
        <Skeleton w="100%" h="56px" />
      </div>
      <div className="hidden md:flex items-center justify-center w-12">
        <Skeleton w="40px" h="40px" rounded="50%" />
      </div>
      <div className="rounded-2xl border border-red-500/30 bg-red-950/30 p-6 space-y-4">
        <Skeleton w="50%" h="14px" />
        <Skeleton w="80px" h="72px" />
        <Skeleton w="100%" h="56px" />
      </div>
    </div>
  );
}
