import { FileText, Database, Code } from "lucide-react";
import { DataFormat } from "@/types/context/setup-wizard-context/types";

export const getFormatIcon = (
  format: DataFormat,
  className: string = "w-4 h-4"
) => {
  switch (format) {
    case "json":
      return <Code className={className} />;
    case "csv":
      return <Database className={className} />;
    case "xml":
      return <FileText className={className} />;
    default:
      return <FileText className={className} />;
  }
};
