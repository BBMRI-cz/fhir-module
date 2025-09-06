"use client";

import { CheckedFormInput } from "@/components/custom/form/CheckedFormInput";
import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useSession } from "next-auth/react";

import z from "zod";
import { UserDetails } from "@/lib/auth-utils";
import { ChangePasswordSchema } from "../schema/ChangePasswordSchema";
import { changePassword } from "@/actions/settings/changePassword";
import { toast } from "sonner";
import { useEffect } from "react";

export const PasswordChangeForm = () => {
  const { data: session, status } = useSession();

  const form = useForm<z.infer<typeof ChangePasswordSchema>>({
    resolver: zodResolver(ChangePasswordSchema),
    defaultValues: {
      currentPassword: "",
      newPassword: "",
      confirmPassword: "",
    },
    mode: "onChange",
    criteriaMode: "all",
  });

  const password = form.watch("newPassword");
  const confirmPassword = form.watch("confirmPassword");

  useEffect(() => {
    form.trigger("confirmPassword");
  }, [password, confirmPassword, form]);

  async function onSubmit(data: z.infer<typeof ChangePasswordSchema>) {
    const result = await changePassword(data, session?.user as UserDetails);
    if (result) {
      toast.success("Password changed successfully");
      form.reset();
    } else {
      toast.error(
        "Failed to change password. Please check your current password."
      );
    }
  }

  if (status === "loading") {
    return <div>Loading...</div>;
  }

  if (!session?.user) {
    return <div>Please log in to change your password.</div>;
  }

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="flex flex-col space-y-6"
      >
        <div className="space-y-4">
          <CheckedFormInput
            control={form.control}
            name="currentPassword"
            label="Current Password"
            placeholder="Enter your current password"
            isPassword={true}
            errors={form.formState.errors}
          />
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
            <Button type="submit" disabled={!form.formState.isValid}>
              Change Password
            </Button>
          </div>
        </div>
      </form>
    </Form>
  );
};
