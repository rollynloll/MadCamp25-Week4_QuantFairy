interface StatusProps {
  status: string;
}

export default function StatusBadge({ status }: StatusProps) {
  const normalized = status === "canceled" ? "cancelled" : status;
  const getColor = () => {
    if (normalized === "filled") return "text-green-500 bg-green-600/10";
    if (normalized === "partial") return "text-blue-500 bg-blue-600/10";
    if (normalized === "cancelled") return "text-gray-500 bg-gray-600/10";
    return "text-yellow-500 bg-yellow-600/10";
  };

  return (
    <span className={`text-xs px-2 py-0.5 rounded font-medium ${getColor()}`}>
      {normalized.toUpperCase()}
    </span>
  );
}
