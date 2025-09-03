import { Button } from "@/components/ui/button";
import { LucideIcon } from "lucide-react";

interface ActionButtonProps {
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
  children: React.ReactNode;
  icon?: LucideIcon;
  variant?:
    | "default"
    | "destructive"
    | "outline"
    | "secondary"
    | "ghost"
    | "link";
  className?: string;
}

export function ActionButton({
  onClick,
  disabled = false,
  loading = false,
  children,
  icon: Icon,
  variant = "default",
  className = "min-w-[100px]",
}: ActionButtonProps) {
  return (
    <Button
      onClick={onClick}
      disabled={disabled}
      variant={variant}
      className={className}
    >
      {Icon && (
        <Icon className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
      )}
      {children}
    </Button>
  );
}
