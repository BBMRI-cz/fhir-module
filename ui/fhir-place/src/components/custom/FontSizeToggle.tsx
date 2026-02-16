"use client";

import { useFontSize } from "@/components/providers/FontSizeProvider";
import { Type } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function FontSizeToggle() {
  const { fontSize, setFontSize } = useFontSize();

  const fontSizes = [
    { value: "small" as const, label: "Small" },
    { value: "medium" as const, label: "Medium" },
    { value: "large" as const, label: "Large" },
  ];

  const currentFontSize =
    fontSizes.find((f) => f.value === fontSize) || fontSizes[1];

  return (
    <div className="flex items-center justify-between">
      <div>
        <h4 className="text-sm font-medium">Font Size</h4>
        <p className="text-sm text-muted-foreground">
          Adjust the font size for better readability
        </p>
      </div>
      <Select value={fontSize} onValueChange={setFontSize}>
        <SelectTrigger className="w-[150px]">
          <SelectValue>
            <div className="flex items-center gap-2">
              <Type className="h-4 w-4" />
              {currentFontSize.label}
            </div>
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {fontSizes.map((fontSizeOption) => (
            <SelectItem key={fontSizeOption.value} value={fontSizeOption.value}>
              <div className="flex items-center gap-2">
                <Type className="h-4 w-4" />
                {fontSizeOption.label}
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
