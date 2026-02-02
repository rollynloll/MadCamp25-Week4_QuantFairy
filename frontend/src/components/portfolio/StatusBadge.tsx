interface StatusProps {
  status: string;
}

export default function StatusBadge({ status }: StatusProps) {
  const getColor = () => {
    if (status === "filled") return "text-green-500 bg-green-600/10";
    if (status === "partial") return "text-blue-500 bg-blue-600/10";
    if (status === "cancelled") return "text-gray-500 bg-gray-600/10";
    return "text-yellow-500 bg-yellow-600/10";
  };

  return (
    <span className={`text-xs px-2 py-0.5 rounded font-medium ${getColor()}`}>
      {status.toUpperCase()}
    </span>
  );
}