"use client";

import { Control, FieldErrors, FieldPath, FieldValues } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { FormControl, FormField, FormItem } from "@/components/ui/form";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { CircleAlert, Eye, EyeOff } from "lucide-react";
import { cn } from "@/lib/utils";
import { useState, useMemo } from "react";

interface CheckedFormInputProps<T extends FieldValues> {
  control: Control<T>;
  name: FieldPath<T>;
  placeholder: string;
  type?: string;
  errors: FieldErrors<T>;
  label?: string;
  isPassword?: boolean;
}

export function CheckedFormInput<T extends FieldValues>({
  control,
  name,
  placeholder,
  type = "text",
  errors,
  label,
  isPassword = false,
}: CheckedFormInputProps<T>) {
  const allMessages = errors[name]?.types
    ? Object.values(errors[name]?.types).flat()
    : undefined;

  const messagesWithIds = useMemo(() => {
    if (!allMessages) return [];

    return allMessages.map((message) => ({
      id: crypto.randomUUID(),
      text: message,
    }));
  }, [allMessages]);

  const [showPassword, setShowPassword] = useState(false);

  let inputType = type;
  if (isPassword) {
    inputType = showPassword ? "text" : "password";
  }

  const hasPasswordToggle = isPassword;
  const hasError = !!allMessages;

  let rightPadding = "pr-3";
  if (hasPasswordToggle && hasError) {
    rightPadding = "pr-20";
  } else if (hasPasswordToggle || hasError) {
    rightPadding = "pr-10";
  }

  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem className="w-full max-w-full">
          {label && (
            <Label htmlFor={name} className="text-sm font-medium">
              {label}
            </Label>
          )}
          <FormControl>
            <div className="relative">
              <Input
                id={name}
                placeholder={placeholder}
                type={inputType}
                {...field}
                className={cn(
                  `w-full ${rightPadding} h-10 sm:h-11 text-sm sm:text-base`,
                  hasError &&
                    "border-red-400 focus:border-red-400 focus:ring-red-400/20"
                )}
              />

              {/* Password toggle button */}
              {hasPasswordToggle && (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className={cn(
                    "absolute top-1/2 transform -translate-y-1/2 h-8 w-8 sm:h-6 sm:w-6 p-0 hover:bg-transparent focus:bg-transparent",
                    hasError ? "right-9 sm:right-10" : "right-1 sm:right-2"
                  )}
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <Eye className="h-4 w-4 text-muted-foreground" />
                  )}
                </Button>
              )}

              {/* Error button */}
              {hasError && (
                <HoverCard openDelay={200}>
                  <HoverCardTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute right-1 sm:right-2 top-1/2 transform -translate-y-1/2 h-8 w-8 sm:h-6 sm:w-6 p-0 hover:bg-transparent focus:bg-transparent"
                      type="button"
                    >
                      <CircleAlert className="text-red-400 h-6 w-6 sm:h-5 sm:w-5" />
                    </Button>
                  </HoverCardTrigger>

                  {/* Desktop HoverCard Content */}
                  <HoverCardContent
                    className="w-80 py-1 hidden lg:block"
                    side="right"
                    sideOffset={20}
                    align="center"
                  >
                    {messagesWithIds.map((messageObj) => (
                      <div
                        key={messageObj.id}
                        className="text-sm text-foreground my-2"
                      >
                        {messageObj.text}
                      </div>
                    ))}
                  </HoverCardContent>

                  {/* Mobile/Tablet HoverCard Content */}
                  <HoverCardContent
                    className="w-64 mx-4 py-1 block lg:hidden"
                    side="bottom"
                    sideOffset={8}
                    align="end"
                  >
                    {messagesWithIds.length > 0 && (
                      <>
                        {messagesWithIds.map((messageObj) => (
                          <div
                            key={messageObj.id}
                            className="text-sm text-foreground"
                          >
                            {messageObj.text}
                          </div>
                        ))}
                      </>
                    )}
                  </HoverCardContent>
                </HoverCard>
              )}
            </div>
          </FormControl>
        </FormItem>
      )}
    />
  );
}
