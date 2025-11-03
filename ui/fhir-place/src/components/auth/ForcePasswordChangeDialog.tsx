"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { validatePassword } from "@/lib/auth/password-validation";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";
import { CheckedFormInput } from "@/components/custom/form/CheckedFormInput";
import { forcePasswordChange } from "@/actions/settings/forcePasswordChange";
import { UserDetails } from "@/lib/auth/auth-utils";

const ForcePasswordChangeSchema = z
  .object({
    newPassword: z.string().superRefine(async (password, ctx) => {
      const validation = await validatePassword(password);
      if (!validation.isValid) {
        for (const error of validation.errors) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: error,
            path: [],
          });
        }
      }
    }),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

interface ForcePasswordChangeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const ForcePasswordChangeDialog = ({
  open,
  onOpenChange,
}: ForcePasswordChangeDialogProps) => {
  const { data: session, update } = useSession();
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<z.infer<typeof ForcePasswordChangeSchema>>({
    resolver: zodResolver(ForcePasswordChangeSchema),
    defaultValues: {
      newPassword: "",
      confirmPassword: "",
    },
    mode: "onChange",
    criteriaMode: "all",
  });

  async function onSubmit(data: z.infer<typeof ForcePasswordChangeSchema>) {
    if (!session?.user) {
      toast.error("Session not found");
      return;
    }

    setIsSubmitting(true);

    try {
      const result = await forcePasswordChange(
        data,
        session.user as UserDetails
      );

      if (result.success) {
        toast.success("Password changed successfully");

        await update({
          ...session,
          user: {
            ...session.user,
            mustChangePassword: false,
          },
        });

        onOpenChange(false);

        router.refresh();
      } else {
        toast.error(result.error || "Failed to change password");
      }
    } catch (error) {
      console.error("Password change error:", error);
      toast.error("An unexpected error occurred");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-md"
        onPointerDownOutside={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>Change Your Password</DialogTitle>
          <DialogDescription>
            You are required to change your password before continuing. Please
            enter a new password.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="flex flex-col space-y-4"
          >
            <CheckedFormInput
              control={form.control}
              name="newPassword"
              label="New Password"
              placeholder="Enter your new password"
              isPassword={true}
              errors={form.formState.errors}
            />

            <CheckedFormInput
              control={form.control}
              name="confirmPassword"
              label="Confirm New Password"
              placeholder="Confirm your new password"
              isPassword={true}
              errors={form.formState.errors}
            />

            <div className="flex justify-end space-x-3 pt-4">
              <Button
                type="submit"
                disabled={!form.formState.isValid || isSubmitting}
                className="w-full"
              >
                {isSubmitting ? "Changing Password..." : "Change Password"}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};
