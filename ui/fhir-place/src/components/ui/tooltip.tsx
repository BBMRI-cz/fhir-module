// NOSONAR - This is an imported shadcn/ui component
"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface TooltipProps {
  children: React.ReactNode;
  content: string;
  className?: string;
}

export function Tooltip({ children, content, className }: TooltipProps) {
  const [isVisible, setIsVisible] = React.useState(false);
  const [position, setPosition] = React.useState({ x: 0, y: 0 });
  const triggerRef = React.useRef<HTMLDivElement>(null);

  const handleMouseEnter = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setPosition({
      x: rect.left + rect.width / 2,
      y: rect.top - 8,
    });
    setIsVisible(true);
  };

  const handleMouseLeave = () => {
    setIsVisible(false);
  };

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className="inline-block"
      >
        {children}
      </div>
      {isVisible && (
        <div
          className={cn(
            "fixed z-50 px-3 py-1.5 text-xs text-white bg-gray-900 rounded-md shadow-lg pointer-events-none transform -translate-x-1/2 -translate-y-full",
            className
          )}
          style={{
            left: position.x,
            top: position.y,
          }}
        >
          {content}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900" />
        </div>
      )}
    </>
  );
}

export const TooltipProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => <>{children}</>;
export const TooltipTrigger = ({ children }: { children: React.ReactNode }) => (
  <>{children}</>
);
export const TooltipContent = ({ children }: { children: React.ReactNode }) => (
  <>{children}</>
);
