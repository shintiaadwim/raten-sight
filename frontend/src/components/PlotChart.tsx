interface PlotPoint { x: number; y: number }

export default function PlotChart({ title, points, xLabel, yLabel, connect = false, zeroLine = false }: {
  title: string;
  points: PlotPoint[];
  xLabel: string;
  yLabel: string;
  connect?: boolean;
  zeroLine?: boolean;
}) {
  const values = points.filter(point => Number.isFinite(point.x) && Number.isFinite(point.y));
  if (!values.length) return <figure className="panel"><figcaption className="font-semibold">{title}</figcaption><p className="mt-3 text-slate-600">Data grafik belum tersedia.</p></figure>;
  const minX = Math.min(0, ...values.map(point => point.x));
  const maxX = Math.max(1, ...values.map(point => point.x));
  const minY = Math.min(0, ...values.map(point => point.y));
  const maxY = Math.max(1, ...values.map(point => point.y));
  const x = (value: number) => 65 + (value - minX) / (maxX - minX) * 430;
  const y = (value: number) => 240 - (value - minY) / (maxY - minY) * 210;
  return <figure className="panel overflow-x-auto" tabIndex={0} aria-label={title}>
    <figcaption className="mb-3 font-semibold">{title}</figcaption>
    <svg viewBox="0 0 540 300" className="min-w-[30rem] w-full" role="img" aria-label={`${title}. Sumbu X ${xLabel}, sumbu Y ${yLabel}. ${values.length} titik.`}>
      {[0, 0.5, 1].map(fraction => <g key={fraction} fill="#475569" fontSize="16">
        <line x1="65" x2="495" y1={240 - fraction * 210} y2={240 - fraction * 210} stroke="#e2e8f0" />
        <text x="58" y={244 - fraction * 210} textAnchor="end">{(minY + fraction * (maxY - minY)).toFixed(1)}</text>
        <text x={65 + fraction * 430} y="262" textAnchor="middle">{(minX + fraction * (maxX - minX)).toFixed(1)}</text>
      </g>)}
      <path d="M 65 20 V 240 H 500" fill="none" stroke="#64748b" />
      {zeroLine && <line x1="65" x2="495" y1={y(0)} y2={y(0)} stroke="#64748b" strokeDasharray="5 4" />}
      {connect && <polyline points={values.map(point => `${x(point.x)},${y(point.y)}`).join(" ")} fill="none" stroke="#4f46e5" strokeWidth="2" />}
      {values.map((point, index) => <circle key={index} cx={x(point.x)} cy={y(point.y)} r={connect ? 4 : 3} fill="#4f46e5" opacity=".65">
        <title>{`${xLabel} ${point.x}, ${yLabel} ${point.y}`}</title>
      </circle>)}
      <text x="280" y="289" textAnchor="middle" fontSize="16" fill="#334155">{xLabel}</text>
      <text x="17" y="135" textAnchor="middle" transform="rotate(-90 17 135)" fontSize="16" fill="#334155">{yLabel}</text>
    </svg>
  </figure>;
}
