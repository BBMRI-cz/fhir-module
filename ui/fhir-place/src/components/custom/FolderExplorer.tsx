"use client";
import { useEffect, useState } from "react";
import {
  FolderIcon,
  FolderOpenIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  LoaderIcon,
  AlertCircleIcon,
  FileIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { FolderTreeRecord } from "@/types/actions/folder/types";
import { getFolders } from "@/actions/folder/folder-actions";
import { Button } from "@/components/ui/button";

interface FolderNodeProps {
  record: FolderTreeRecord;
  level?: number;
  selectedPath?: string;
  onSelect?: (record: FolderTreeRecord) => void;
}

interface ExpandIconProps {
  loading: boolean;
  expanded: boolean;
  hasChildren: boolean;
}

function ExpandIcon({ loading, expanded, hasChildren }: ExpandIconProps) {
  if (loading) {
    return <LoaderIcon className="w-3 h-3 animate-spin text-gray-500" />;
  }

  if (!hasChildren) {
    return null;
  }

  return expanded ? (
    <ChevronDownIcon className="w-3 h-3 text-gray-600 dark:text-gray-400" />
  ) : (
    <ChevronRightIcon className="w-3 h-3 text-gray-600 dark:text-gray-400" />
  );
}

interface FolderItemIconProps {
  isFile: boolean;
  expanded: boolean;
}

function FolderItemIcon({ isFile, expanded }: FolderItemIconProps) {
  if (isFile) {
    return <FileIcon className="w-4 h-4 text-gray-500" />;
  }

  return expanded ? (
    <FolderOpenIcon className="w-4 h-4 text-primary" />
  ) : (
    <FolderIcon className="w-4 h-4 text-primary" />
  );
}

interface ErrorMessageProps {
  error: string;
  indentLevel: number;
}

function ErrorMessage({ error, indentLevel }: ErrorMessageProps) {
  return (
    <div
      className="text-xs text-red-600 dark:text-red-400 py-1 px-2 ml-6"
      style={{ paddingLeft: `${indentLevel + 32}px` }}
    >
      {error}
    </div>
  );
}

interface FolderChildrenProps {
  loaded: boolean;
  indentLevel: number;
  isEmpty: boolean;
  children?: React.ReactNode;
}

function FolderChildren({
  loaded,
  indentLevel,
  isEmpty,
  children,
}: FolderChildrenProps) {
  if (isEmpty && loaded) {
    return (
      <div
        className="text-xs py-1 px-2 italic text-gray-500"
        style={{ paddingLeft: `${indentLevel + 32}px` }}
      >
        Empty folder
      </div>
    );
  }

  return <>{children}</>;
}

function FolderNode({
  record,
  level = 0,
  selectedPath,
  onSelect,
}: FolderNodeProps) {
  const [expanded, setExpanded] = useState(false);
  const [children, setChildren] = useState<FolderTreeRecord[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isDirectory = record.isDirectory !== false;
  const isFile = !isDirectory;
  const hasChildren =
    isDirectory && (children.length > 0 || (!loaded && !error));
  const indentLevel = level * 10;
  const isSelected = selectedPath === record.path;

  const toggleExpand = async () => {
    if (isFile) return;

    if (!expanded && !loaded) {
      setLoading(true);
      setError(null);
      try {
        const data = await getFolders(record.path, true);
        setChildren(data);
        setLoaded(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load folders");
        console.error("Error loading folders:", err);
      } finally {
        setLoading(false);
      }
    }
    setExpanded(!expanded);
  };

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isFile) return;
    onSelect?.(record);
  };

  const handleExpandClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    toggleExpand();
  };

  const handleExpandKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      e.stopPropagation();
      toggleExpand();
    }
  };

  return (
    <div className="select-none">
      <Button
        variant="ghost"
        className={cn(
          "flex items-center gap-2 py-1 px-2 rounded-md transition-colors w-full justify-start h-auto font-normal text-left",
          isFile
            ? "cursor-not-allowed opacity-60"
            : "hover:bg-gray-100 dark:hover:bg-gray-900",
          "group",
          !isFile &&
            isSelected &&
            "bg-accent dark:bg-accent border border-border"
        )}
        style={{ paddingLeft: `${indentLevel + 8}px` }}
        onClick={handleClick}
        disabled={isFile}
      >
        <span
          className="w-4 h-4 flex items-center justify-center rounded p-0 cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors"
          onClick={handleExpandClick}
          onKeyDown={handleExpandKeyDown}
          aria-label={expanded ? "Collapse folder" : "Expand folder"}
          role="button"
          tabIndex={0}
        >
          <ExpandIcon
            loading={loading}
            expanded={expanded}
            hasChildren={hasChildren}
          />
        </span>

        <div className="w-4 h-4 flex items-center justify-center">
          <FolderItemIcon isFile={isFile} expanded={expanded} />
        </div>

        <span
          className={cn(
            "text-sm font-medium",
            "truncate flex-1",
            !isFile && isSelected && "text-accent-foreground font-semibold"
          )}
        >
          {record.name}
        </span>

        {error && (
          <AlertCircleIcon className="w-4 h-4 text-red-500 flex-shrink-0" />
        )}
      </Button>

      {error && expanded && (
        <ErrorMessage error={error} indentLevel={indentLevel} />
      )}

      {expanded && !error && isDirectory && (
        <div className="transition-all duration-200 ease-in-out">
          <FolderChildren
            loaded={loaded}
            indentLevel={indentLevel}
            isEmpty={children.length === 0}
          >
            {children.map((child) => (
              <FolderNode
                key={child.path}
                record={child}
                level={level + 1}
                selectedPath={selectedPath}
                onSelect={onSelect}
              />
            ))}
          </FolderChildren>
        </div>
      )}
    </div>
  );
}

interface FolderExplorerProps {
  onFolderSelect?: (record: FolderTreeRecord) => void;
  selectedPath?: string;
}

export default function FolderExplorer({
  onFolderSelect,
  selectedPath,
}: FolderExplorerProps) {
  const [records, setRecords] = useState<FolderTreeRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [internalSelectedPath, setInternalSelectedPath] = useState<
    string | undefined
  >(selectedPath);

  useEffect(() => {
    const loadRootFolders = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await getFolders("", true);
        setRecords(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load folders");
        console.error("Error loading root folders:", err);
      } finally {
        setLoading(false);
      }
    };

    loadRootFolders();
  }, []);

  useEffect(() => {
    setInternalSelectedPath(selectedPath);
  }, [selectedPath]);

  const handleFolderSelect = (record: FolderTreeRecord) => {
    setInternalSelectedPath(record.path);
    onFolderSelect?.(record);
  };

  const currentSelectedPath = selectedPath ?? internalSelectedPath;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="flex items-center gap-2">
          <LoaderIcon className="w-4 h-4 animate-spin" />
          <span className="text-sm">Loading folders...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 py-4 px-2 text-red-600 dark:text-red-400">
        <AlertCircleIcon className="w-4 h-4 flex-shrink-0" />
        <span className="text-sm">{error}</span>
      </div>
    );
  }

  if (records.length === 0) {
    return <div className="py-4 px-2 text-sm italic">No items found</div>;
  }

  return (
    <div className="w-full">
      <div className="border rounded-lg shadow-sm">
        <div className="p-3 border-b">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <FolderIcon className="w-4 h-4" />
            Folder Explorer
          </h3>
        </div>
        <div className="p-2 max-h-96 overflow-y-auto">
          {records.map((record) => (
            <FolderNode
              key={record.path}
              record={record}
              selectedPath={currentSelectedPath}
              onSelect={handleFolderSelect}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
