// A glowing, slowly turning wireframe globe rising from the page's start side
// (partly off-screen) behind every page —
// decoration only (aria-hidden, ignores the pointer, sits behind all
// content). The "rotation" is meridian ellipses sweeping their width in
// staggered phase; a sphere gradient, soft halo, and a shimmering specular
// highlight give it shine; a small satellite orbits on a tilted ring.
// Inline SVG, no image assets, so it also works on the closed network.
// Motion is skipped entirely when the user prefers reduced motion.
const SIZE = 400;
const CENTER = SIZE / 2;
const RADIUS = 150;
const ORBIT_RADIUS = RADIUS + 26;
const MERIDIANS = 8;
const SPIN_SECONDS = 28;
const PARALLEL_LATITUDES = [-60, -30, 0, 30, 60];

const prefersReducedMotion =
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export default function GlobeBackdrop() {
  return (
    <svg
      aria-hidden="true"
      viewBox={`0 0 ${SIZE} ${SIZE}`}
      className="pointer-events-none fixed -start-64 top-[62%] -z-10 h-[min(115vh,1000px)] w-[min(115vh,1000px)] -translate-y-1/2 text-sky-500 opacity-45"
      fill="none"
      stroke="currentColor"
      strokeWidth="1"
    >
      <defs>
        {/* Soft halo around the planet. */}
        <radialGradient id="globe-halo">
          <stop offset="70%" stopColor="currentColor" stopOpacity="0.35" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
        </radialGradient>
        {/* Sphere shading, lit from the top-left. */}
        <radialGradient id="globe-body" cx="38%" cy="32%" r="75%">
          <stop offset="0%" stopColor="#e0f2fe" stopOpacity="0.55" />
          <stop offset="45%" stopColor="currentColor" stopOpacity="0.18" />
          <stop offset="100%" stopColor="#1e3a8a" stopOpacity="0.28" />
        </radialGradient>
        {/* Specular highlight. */}
        <radialGradient id="globe-shine" cx="34%" cy="28%" r="30%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
        </radialGradient>
        <filter id="globe-glow" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <circle cx={CENTER} cy={CENTER} r={RADIUS + 40} fill="url(#globe-halo)" stroke="none" />
      <circle cx={CENTER} cy={CENTER} r={RADIUS} fill="url(#globe-body)" stroke="none" />

      <g transform={`rotate(-23.4 ${CENTER} ${CENTER})`} filter="url(#globe-glow)">
        <circle cx={CENTER} cy={CENTER} r={RADIUS} strokeWidth="1.75" />

        {PARALLEL_LATITUDES.map((latitude) => {
          const radians = (latitude * Math.PI) / 180;
          const y = CENTER - RADIUS * Math.sin(radians);
          const halfWidth = RADIUS * Math.cos(radians);
          return (
            <ellipse
              key={latitude}
              cx={CENTER}
              cy={y}
              rx={halfWidth}
              ry={halfWidth * 0.12}
              strokeWidth={latitude === 0 ? 1.4 : 1}
              strokeDasharray={latitude === 0 ? undefined : "3 4"}
            />
          );
        })}

        {Array.from({ length: MERIDIANS }, (_, index) => (
          <ellipse key={index} cx={CENTER} cy={CENTER} rx={RADIUS} ry={RADIUS}>
            {!prefersReducedMotion && (
              <animate
                attributeName="rx"
                values={`0;${RADIUS};0`}
                dur={`${SPIN_SECONDS}s`}
                begin={`${-(index * SPIN_SECONDS) / MERIDIANS}s`}
                repeatCount="indefinite"
              />
            )}
          </ellipse>
        ))}
      </g>

      <circle cx={CENTER} cy={CENTER} r={RADIUS} fill="url(#globe-shine)" stroke="none">
        {!prefersReducedMotion && (
          <animate
            attributeName="opacity"
            values="0.55;1;0.55"
            dur="6s"
            repeatCount="indefinite"
          />
        )}
      </circle>

      {/* Tilt the ring and the satellite together — animateMotion follows
          the path's raw geometry, ignoring a transform on the path itself. */}
      <g transform={`rotate(18 ${CENTER} ${CENTER})`}>
        <ellipse
          id="globe-orbit"
          cx={CENTER}
          cy={CENTER}
          rx={ORBIT_RADIUS}
          ry={ORBIT_RADIUS * 0.28}
          strokeDasharray="2 6"
        />
        <circle
          r="4.5"
          fill="currentColor"
          stroke="none"
          filter="url(#globe-glow)"
          cx={prefersReducedMotion ? CENTER + ORBIT_RADIUS : 0}
          cy={prefersReducedMotion ? CENTER : 0}
        >
          {!prefersReducedMotion && (
            <animateMotion dur="40s" repeatCount="indefinite">
              <mpath href="#globe-orbit" />
            </animateMotion>
          )}
        </circle>
      </g>
    </svg>
  );
}
