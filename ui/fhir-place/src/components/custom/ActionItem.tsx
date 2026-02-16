import { Badge } from "@/components/ui/badge";
import { ActionButton } from "./ActionButton";
import { LucideIcon } from "lucide-react";

export interface ActionResult {
  success: boolean;
  message: string;
}

interface ActionItemProps {
  title: string;
  description: string;
  buttonText: string;
  onAction: () => void;
  isLoading: boolean;
  result?: ActionResult;
  isFading?: boolean;
  icon?: LucideIcon;
  variant?:
    | "default"
    | "destructive"
    | "outline"
    | "secondary"
    | "ghost"
    | "link";
  disabled?: boolean;
  children?: React.ReactNode;
}

export function ActionItem({
  title,
  description,
  buttonText,
  onAction,
  isLoading,
  result,
  isFading = false,
  icon,
  variant = "default",
  disabled = false,
  children,
}: ActionItemProps) {
  const resultBadge = result && (
    <Badge
      variant="outline"
      className={`
        transition-opacity duration-1000 ease-in-out
        ${isFading ? "opacity-0" : "opacity-100"}
        ${
          result.success
            ? "text-green-400 border-green-400"
            : "text-red-400 border-red-400"
        }
      `}
    >
      {result.success ? "Success" : "Failed"}
    </Badge>
  );

  return (
    <div className="flex items-center justify-between">
      <div className="space-y-1">
        <p className="text-sm font-medium">{title}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <div className="flex items-center gap-2">
        {resultBadge}
        {children || (
          <ActionButton
            onClick={onAction}
            disabled={disabled}
            loading={isLoading}
            icon={icon}
            variant={variant}
          >
            {buttonText}
          </ActionButton>
        )}
      </div>
    </div>
  );
}
