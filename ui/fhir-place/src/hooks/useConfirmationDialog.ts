import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import z from "zod";
import { toast } from "sonner";
import { ConfirmDeleteSchema } from "@/app/(authorized)/backend-control/form/schema";

export function useConfirmationDialog(
  confirmationMessage: string,
  onConfirmedAction: () => void
) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const form = useForm<z.infer<typeof ConfirmDeleteSchema>>({
    resolver: zodResolver(ConfirmDeleteSchema),
    defaultValues: {
      confirmInput: "",
    },
  });

  const handleConfirm = (data: z.infer<typeof ConfirmDeleteSchema>) => {
    if (data.confirmInput !== confirmationMessage) {
      toast.error("Confirmation is incorrect");
      return;
    }

    setIsDialogOpen(false);
    onConfirmedAction();
  };

  const handleDialogChange = (open: boolean) => {
    setIsDialogOpen(open);
    if (!open) {
      form.reset();
    }
  };

  return {
    isDialogOpen,
    form,
    confirmationMessage,
    handleConfirm,
    handleDialogChange,
  };
}
