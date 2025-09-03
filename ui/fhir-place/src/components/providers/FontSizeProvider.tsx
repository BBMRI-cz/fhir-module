"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useMemo,
  ReactNode,
} from "react";

type FontSize = "small" | "medium" | "large";

interface FontSizeContextType {
  fontSize: FontSize;
  setFontSize: (fontSize: FontSize) => void;
}

const FontSizeContext = createContext<FontSizeContextType | undefined>(
  undefined
);

export function useFontSize() {
  const context = useContext(FontSizeContext);
  if (!context) {
    throw new Error("useFontSize must be used within a FontSizeProvider");
  }
  return context;
}

interface FontSizeProviderProps {
  children: ReactNode;
}

export function FontSizeProvider({ children }: FontSizeProviderProps) {
  const [fontSize, setFontSize] = useState<FontSize>("medium");

  useEffect(() => {
    const savedFontSize = localStorage.getItem("fontSize") as FontSize | null;
    if (savedFontSize && ["small", "medium", "large"].includes(savedFontSize)) {
      setFontSize(savedFontSize);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("fontSize", fontSize);

    const root = document.documentElement;
    root.classList.remove("font-small", "font-medium", "font-large");
    root.classList.add(`font-${fontSize}`);
  }, [fontSize]);

  const contextValue = useMemo(
    () => ({ fontSize, setFontSize }),
    [fontSize, setFontSize]
  );

  return (
    <FontSizeContext.Provider value={contextValue}>
      {children}
    </FontSizeContext.Provider>
  );
}
