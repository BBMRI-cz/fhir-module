import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import z from "zod";
import { toast } from "sonner";
import { ConfirmDeleteSchema } from "@/app/(authorized)/backend-control/form/schema";

const deleteAllConfirmMessage = "DELETE ALL";

export function useDeleteDialog(onConfirmedDelete: () => void) {
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const form = useForm<z.infer<typeof ConfirmDeleteSchema>>({
    resolver: zodResolver(ConfirmDeleteSchema),
    defaultValues: {
      confirmInput: "",
    },
  });

  const handleDelete = (data: z.infer<typeof ConfirmDeleteSchema>) => {
    if (data.confirmInput !== deleteAllConfirmMessage) {
      toast.error("Confirmation is incorrect");
      return;
    }

    setIsDeleteDialogOpen(false);
    onConfirmedDelete();
  };

  const handleDialogChange = (open: boolean) => {
    setIsDeleteDialogOpen(open);
    if (!open) {
      form.reset();
    }
  };

  return {
    isDeleteDialogOpen,
    form,
    deleteAllConfirmMessage,
    handleDelete,
    handleDialogChange,
  };
}
