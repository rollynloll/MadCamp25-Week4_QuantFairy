interface StateProps {
  state: string; 
  small?: boolean
}

export default function StateToggle({ state, small }: StateProps) {
  const getColor = () => {
    if (state === "running") return "text-green-500 bg-green-600/10";
    if (state === "paused") return "text-yellow-500 bg-yellow-600/10";
    if (state === "stopped") return "text-red-500 bg-red-600/10";
    return "text-gray-500 bg-gray-600/10";
  };

  return (
    <span className={`${small ? "text-xs px-2 py-0.5" : "text-xs px-2 py-1"} rounded font-medium ${getColor()}`}>
      {state.toUpperCase()}
    </span>
  );
}
