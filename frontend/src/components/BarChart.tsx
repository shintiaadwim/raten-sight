import type { DistributionEntry } from "@/types/api";

interface BarChartProps {
  title: string;
  data: DistributionEntry[];
  color?: "indigo" | "blue" | "violet";
}

const colorMap = {
  indigo: "bg-indigo-500",
  blue: "bg-blue-500",
  violet: "bg-violet-500",
};

const textMap = {
  indigo: "text-indigo-700",
  blue: "text-blue-700",
  violet: "text-violet-700",
};

export default function BarChart({
  title,
  data,
  color = "indigo",
}: BarChartProps) {
  const maxCount = Math.max(...data.map((d) => d.count), 1);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <h3 className="font-semibold text-slate-700 mb-1">{title}</h3>
      <p className="mb-4 text-sm text-slate-500">Jumlah pelanggan</p>
      {data.length === 0 && <p className="text-sm text-slate-600">Distribusi belum tersedia.</p>}
      <div className="flex flex-col gap-3">
        {data.map((entry) => {
          const widthPct = Math.round((entry.count / maxCount) * 100);
          return (
            <div key={entry.label} className="flex flex-col gap-1">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">{entry.label}</span>
                <span
                  className={`text-sm font-semibold ${textMap[color]}`}
                >
                  {entry.count}
                </span>
              </div>
              <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${colorMap[color]} transition-all duration-500`}
                  style={{ width: `${widthPct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
