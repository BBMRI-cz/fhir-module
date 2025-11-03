import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState, useEffect } from "react";
import { Edit2 } from "lucide-react";

interface CustomValueSelectProps {
  value: string;
  onValueChange: (value: string) => void;
  availableOptions: string[];
  allowCustomValues: boolean;
  placeholder?: string;
}

export default function CustomValueSelect({
  value,
  onValueChange,
  availableOptions,
  allowCustomValues,
  placeholder = "Select value",
}: CustomValueSelectProps) {
  const [isCustom, setIsCustom] = useState(false);
  const [customInput, setCustomInput] = useState("");

  useEffect(() => {
    const isValueCustom = Boolean(value && !availableOptions.includes(value));
    setIsCustom(isValueCustom);
    if (isValueCustom) {
      setCustomInput(value);
    }
  }, [value, availableOptions]);

  const handleSelectChange = (newValue: string) => {
    if (newValue === "__CUSTOM__") {
      setIsCustom(true);
      setCustomInput("");
    } else {
      setIsCustom(false);
      onValueChange(newValue);
    }
  };

  const handleCustomInputChange = (inputValue: string) => {
    setCustomInput(inputValue);
    onValueChange(inputValue);
  };

  const selectOptions = [...availableOptions];

  if (value && !availableOptions.includes(value)) {
    selectOptions.unshift(value);
  }

  if (isCustom && allowCustomValues) {
    return (
      <div className="relative">
        <Input
          placeholder="Enter custom value"
          value={customInput}
          onChange={(e) => handleCustomInputChange(e.target.value)}
          className="h-9 text-sm font-mono pr-20"
          autoFocus
        />
        <button
          onClick={() => {
            setIsCustom(false);
            onValueChange("");
          }}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-muted-foreground hover:text-foreground underline"
        >
          Use dropdown
        </button>
      </div>
    );
  }

  return (
    <Select value={value} onValueChange={handleSelectChange}>
      <SelectTrigger className="h-9 text-xs sm:text-sm w-full">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent className="w-[var(--radix-select-trigger-width)] text-sm sm:text-md">
        {selectOptions.map((option) => (
          <SelectItem key={option} value={option}>
            <span className="font-mono truncate block text-xs sm:text-sm">
              {option}
            </span>
          </SelectItem>
        ))}
        {allowCustomValues && (
          <>
            <div className="px-2 py-1.5 text-xs text-muted-foreground border-t">
              Or enter custom value:
            </div>
            <SelectItem value="__CUSTOM__" className="text-xs sm:text-sm">
              <div className="flex items-center gap-2">
                <Edit2 className="h-3 w-3" />
                <span>Add custom value...</span>
              </div>
            </SelectItem>
          </>
        )}
      </SelectContent>
    </Select>
  );
}
