"use client";

import { useTheme } from "@/components/providers/ThemeProvider";
import { Sun, Moon, Monitor } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  const themes = [
    { value: "light" as const, label: "Light", icon: Sun },
    { value: "dark" as const, label: "Dark", icon: Moon },
    { value: "system" as const, label: "System", icon: Monitor },
  ];

  const currentTheme = themes.find((t) => t.value === theme) || themes[2];

  return (
    <div className="flex items-center justify-between">
      <div>
        <h4 className="text-sm font-medium">Theme</h4>
        <p className="text-sm text-muted-foreground">
          Choose between light and dark mode
        </p>
      </div>
      <Select value={theme} onValueChange={setTheme}>
        <SelectTrigger className="w-[150px]">
          <SelectValue>
            <div className="flex items-center gap-2">
              <currentTheme.icon className="h-4 w-4" />
              {currentTheme.label}
            </div>
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {themes.map((themeOption) => {
            const Icon = themeOption.icon;
            return (
              <SelectItem key={themeOption.value} value={themeOption.value}>
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4" />
                  {themeOption.label}
                </div>
              </SelectItem>
            );
          })}
        </SelectContent>
      </Select>
    </div>
  );
}
