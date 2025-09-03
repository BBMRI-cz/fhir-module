"use client";

import { CheckedFormInput } from "@/components/custom/form/CheckedFormInput";
import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useSession } from "next-auth/react";

import z from "zod";
import { UserDetails } from "@/lib/auth-utils";
import { ChangeUserDetailsSchema } from "../schema/ChangeUserDetailsSchema";
import { changeUserDetails } from "@/actions/settings/changeUserDetails";
import { toast } from "sonner";

export const UserDetailsForm = () => {
  const { data: session, status, update } = useSession();

  const currentUser = session?.user as UserDetails;

  const form = useForm<z.infer<typeof ChangeUserDetailsSchema>>({
    resolver: zodResolver(ChangeUserDetailsSchema),
    defaultValues: {
      firstName: "",
      lastName: "",
      email: "",
    },
    mode: "onChange",
  });

  async function onSubmit(data: z.infer<typeof ChangeUserDetailsSchema>) {
    const user = session?.user as UserDetails;

    const hasChanges =
      data.firstName !== user?.firstName ||
      data.lastName !== user?.lastName ||
      data.email !== user?.email;

    if (!hasChanges) {
      toast.info("No changes detected");
      return;
    }

    const result = await changeUserDetails(data, session?.user as UserDetails);
    if (result) {
      toast.success("User details updated successfully");

      await update();

      form.reset({
        firstName: "",
        lastName: "",
        email: "",
      });
    } else {
      toast.error("Failed to update user details");
    }
  }

  if (status === "loading") {
    return <div>Loading...</div>;
  }

  if (!session?.user) {
    return <div>Please log in to view this form.</div>;
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
            name="firstName"
            label="First Name"
            placeholder={currentUser?.firstName || "Enter your first name"}
            errors={form.formState.errors}
          />
          <CheckedFormInput
            control={form.control}
            name="lastName"
            label="Last Name"
            placeholder={currentUser?.lastName || "Enter your last name"}
            errors={form.formState.errors}
          />
          <CheckedFormInput
            control={form.control}
            name="email"
            label="Email"
            placeholder={currentUser?.email || "Enter your email address"}
            errors={form.formState.errors}
          />
          <div className="flex justify-end space-x-3 pt-4">
            <Button type="submit">Save Changes</Button>
          </div>
        </div>
      </form>
    </Form>
  );
};
