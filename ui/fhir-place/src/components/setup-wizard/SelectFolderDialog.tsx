import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogTitle,
  DialogHeader,
  DialogFooter,
} from "@/components/ui/dialog";
import FolderExplorer from "@/components/custom/FolderExplorer";
import { Button } from "@/components/ui/button";
import { ReactNode, useState } from "react";
import { FolderTreeRecord } from "@/types/actions/folder/types";

export interface SelectFolderDialogProps {
  children: ReactNode;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (folder: string) => void;
}
export default function SelectFolderDialog({
  children,
  isOpen,
  onOpenChange,
  onConfirm,
}: SelectFolderDialogProps) {
  const [folderSelected, setFolderSelected] = useState<FolderTreeRecord | null>(
    null
  );

  function onFolderSelect(folder: FolderTreeRecord) {
    setFolderSelected(folder);
  }

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            Select folder from which the data will be uploaded
          </DialogTitle>
        </DialogHeader>
        <div className="w-full overflow-x-auto">
          <FolderExplorer onFolderSelect={onFolderSelect} />
        </div>
        <DialogFooter>
          <Button
            type="submit"
            disabled={!folderSelected}
            onClick={() => {
              onConfirm(folderSelected!.path);
              onOpenChange(false);
            }}
          >
            Select folder
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
