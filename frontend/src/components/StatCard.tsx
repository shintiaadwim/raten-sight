interface StatCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  accent?: "default" | "red" | "green" | "blue";
}

const accentMap = {
  default: "border-l-indigo-500",
  red: "border-l-red-500",
  green: "border-l-green-500",
  blue: "border-l-blue-500",
};

const valueColorMap = {
  default: "text-slate-900",
  red: "text-red-600",
  green: "text-green-600",
  blue: "text-blue-600",
};

export default function StatCard({
  label,
  value,
  subtitle,
  accent = "default",
}: StatCardProps) {
  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-slate-200 border-l-4 ${accentMap[accent]} p-5 flex flex-col gap-1`}
    >
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
        {label}
      </p>
      <p className={`text-3xl font-bold ${valueColorMap[accent]}`}>{value}</p>
      {subtitle && (
        <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>
      )}
    </div>
  );
}
