import type { ModelInfoData } from "@/types/api";

interface ModelInfoCardProps {
  data: ModelInfoData;
}

interface CardProps {
  title: string;
  algorithm: string;
  features: string[];
  extra?: React.ReactNode;
}

function Card({ title, algorithm, features, extra }: CardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col gap-3">
      <div>
        <p className="text-xs font-semibold text-indigo-500 uppercase tracking-wide mb-1">
          {title}
        </p>
        <p className="text-lg font-bold text-slate-800">{algorithm}</p>
      </div>
      <div>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
          Fitur
        </p>
        <div className="flex flex-wrap gap-1.5">
          {features.map((f) => (
            <span
              key={f}
              className="px-2 py-0.5 bg-indigo-50 text-indigo-700 text-xs rounded-md border border-indigo-100 font-mono"
            >
              {f}
            </span>
          ))}
        </div>
      </div>
      {extra && <div>{extra}</div>}
    </div>
  );
}

export default function ModelInfoCard({ data }: ModelInfoCardProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Classification */}
      <Card
        title="Classification"
        algorithm={data.classification.algorithm}
        features={data.classification.features}
        extra={
          <div className="text-xs text-slate-500 space-y-1">
            <div>
              <span className="font-medium text-slate-600">Positive class:</span>{" "}
              {data.classification.positive_class}
            </div>
            <div>
              <span className="font-medium text-slate-600">Threshold:</span>{" "}
              {data.classification.threshold}
            </div>
          </div>
        }
      />

      {/* Clustering */}
      <Card
        title="Clustering"
        algorithm={data.clustering.algorithm}
        features={data.clustering.features}
        extra={
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
              Segmen
            </p>
            <div className="flex flex-col gap-1.5">
              {data.clustering.segments.map((seg) => (
                <div
                  key={seg.segment_id}
                  className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2 text-xs"
                >
                  <span className="text-slate-700 font-medium">
                    {seg.segment_name}
                  </span>
                  <span className="text-slate-400">
                    {seg.customer_count} pelanggan
                  </span>
                </div>
              ))}
            </div>
          </div>
        }
      />

      {/* Regression */}
      <Card
        title="Regression"
        algorithm={data.regression.algorithm}
        features={data.regression.features}
        extra={
          <div className="text-xs text-slate-500 space-y-1">
            <div>
              <span className="font-medium text-slate-600">Target:</span>{" "}
              {data.regression.target}
            </div>
            <div>
              <span className="font-medium text-slate-600">Unit:</span>{" "}
              {data.regression.unit}
            </div>
          </div>
        }
      />
    </div>
  );
}
