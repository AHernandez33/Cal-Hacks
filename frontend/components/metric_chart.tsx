"use client";
type Series = { label: string; color: string; values: number[] };
export default function MetricChart({
  title,
  description,
  rounds,
  series,
  percentage = false,
}: {
  title: string;
  description: string;
  rounds: number[];
  series: Series[];
  percentage?: boolean;
}) {
  const maximum = percentage
    ? 1
    : Math.max(0.1, ...series.flatMap((s) => s.values)) * 1.15;
  const x = (i: number) => 65 + (i / Math.max(1, rounds.length - 1)) * 535;
  const y = (v: number) => 200 - (v / maximum) * 170;
  return (
    <figure className="metric-chart">
      <figcaption>
        <h3>{title}</h3>
        <p className="muted">{description}</p>
      </figcaption>
      <svg
        viewBox="0 0 640 250"
        role="img"
        aria-label={`${title}. ${description}. Exact values are in the training history table.`}
      >
        <title>{title}</title>
        <desc>
          {series
            .map(
              (s) =>
                `${s.label}: ${s.values.map((v) => v.toFixed(3)).join(", ")}`,
            )
            .join(". ")}
        </desc>
        {[0, 0.25, 0.5, 0.75, 1].map((f) => (
          <g key={f}>
            <line
              x1="65"
              y1={y(maximum * f)}
              x2="600"
              y2={y(maximum * f)}
              stroke="#00ed6426"
            />
            <text
              x="54"
              y={y(maximum * f) + 4}
              textAnchor="end"
              fill="#a6bcb2"
              fontSize="11"
            >
              {percentage
                ? `${Math.round(f * 100)}%`
                : (maximum * f).toFixed(2)}
            </text>
          </g>
        ))}
        {rounds.map((round, i) => (
          <text
            key={round}
            x={x(i)}
            y="221"
            textAnchor="middle"
            fill="#a6bcb2"
            fontSize="11"
          >
            {round}
          </text>
        ))}
        <text x="330" y="244" textAnchor="middle" fill="#a6bcb2" fontSize="11">
          Training round
        </text>
        {series.map((s) => (
          <g key={s.label}>
            <polyline
              points={s.values
                .map((value, i) => `${x(i)},${y(value)}`)
                .join(" ")}
              fill="none"
              stroke={s.color}
              strokeWidth="2.5"
            />
            {s.values.map((value, i) => (
              <circle key={i} cx={x(i)} cy={y(value)} r="3" fill={s.color}>
                <title>
                  {s.label}, round {rounds[i]}: {value.toFixed(4)}
                </title>
              </circle>
            ))}
          </g>
        ))}
      </svg>
      <div className="chart-legend">
        {series.map((s) => (
          <span key={s.label}>
            <i style={{ background: s.color }} />
            {s.label}
          </span>
        ))}
      </div>
    </figure>
  );
}
