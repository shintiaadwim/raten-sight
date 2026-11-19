interface StatusBadgeProps {
  status: "ready" | "preparing" | "failed" | string;
}

const statusConfig: Record<
  string,
  { label: string; className: string }
> = {
  ready: {
    label: "Ready",
    className: "bg-green-100 text-green-800 border border-green-200",
  },
  preparing: {
    label: "Preparing",
    className: "bg-yellow-100 text-yellow-800 border border-yellow-200",
  },
  failed: {
    label: "Failed",
    className: "bg-red-100 text-red-800 border border-red-200",
  },
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status] ?? {
    label: status,
    className: "bg-gray-100 text-gray-700 border border-gray-200",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm font-semibold ${config.className}`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          status === "ready"
            ? "bg-green-500"
            : status === "preparing"
            ? "bg-yellow-500"
            : status === "failed"
            ? "bg-red-500"
            : "bg-gray-400"
        }`}
      />
      {config.label}
    </span>
  );
}
