"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { CheckedFormInput } from "@/components/custom/form/CheckedFormInput";
import { Form } from "@/components/ui/form";
import { ReactNode } from "react";
import { UseFormReturn } from "react-hook-form";
import { z } from "zod";
import { ConfirmDeleteSchema } from "@/app/(authorized)/backend-control/form/schema";

export interface ConfirmationDialogProps {
  children: ReactNode;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmationMessage: string;
  confirmButtonText: string;
  form: UseFormReturn<z.infer<typeof ConfirmDeleteSchema>>;
  onConfirm: (data: z.infer<typeof ConfirmDeleteSchema>) => void;
  isLoading?: boolean;
}

export function ConfirmationDialog({
  children,
  isOpen,
  onOpenChange,
  title,
  description,
  confirmationMessage,
  confirmButtonText,
  form,
  onConfirm,
  isLoading = false,
}: ConfirmationDialogProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>
            {description} To proceed, please type &quot;{confirmationMessage}
            &quot; in the input field below.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onConfirm)}>
            <CheckedFormInput
              control={form.control}
              type="text"
              name="confirmInput"
              placeholder={confirmationMessage}
              errors={form.formState.errors}
            />
            <DialogFooter className="flex justify-end pt-4">
              <DialogClose asChild>
                <Button variant="outline">Cancel</Button>
              </DialogClose>
              <Button
                type="submit"
                disabled={isLoading}
                variant="destructive"
                className="min-w-[100px]"
              >
                {confirmButtonText}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
