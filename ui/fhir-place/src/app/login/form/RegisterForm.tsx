"use client";

import { useForm } from "react-hook-form";
import { RegisterFormSchema } from "./schema";
import z from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Form } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { CheckedFormInput } from "@/components/custom/form/CheckedFormInput";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useSession } from "next-auth/react";

const RegisterForm = () => {
  const router = useRouter();
  const { update } = useSession();

  const form = useForm<z.infer<typeof RegisterFormSchema>>({
    resolver: zodResolver(RegisterFormSchema),
    defaultValues: {
      firstName: "",
      lastName: "",
      email: "",
      username: "",
      password: "",
      confirmPassword: "",
    },
    mode: "onChange",
    criteriaMode: "all",
  });

  const password = form.watch("password");
  const confirmPassword = form.watch("confirmPassword");

  useEffect(() => {
    form.trigger("confirmPassword");
  }, [password, confirmPassword, form]);

  async function onSubmit(data: z.infer<typeof RegisterFormSchema>) {
    const { registerAction } = await import(
      "../../../actions/auth-management/register"
    );

    try {
      const result = await registerAction(data);

      if (result.success) {
        toast.success("Registration Successful", {
          description: result.message,
        });
        
        await update();
        router.refresh();
        router.push("/dashboard");
      } else {
        toast.error("Registration Failed", {
          description: result.message,
        });
      }
    } catch (error) {
      toast.error("Registration Failed", {
        description: "An unexpected error occurred. Please try again.",
      });
      console.error("Registration error:", error);
    }
  }

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="pt-4 sm:pt-8 flex flex-col w-full space-y-4"
      >
        <CheckedFormInput
          control={form.control}
          name="firstName"
          placeholder="First Name"
          errors={form.formState.errors}
        />
        <CheckedFormInput
          control={form.control}
          name="lastName"
          placeholder="Last Name"
          errors={form.formState.errors}
        />
        <CheckedFormInput
          control={form.control}
          name="email"
          placeholder="Email"
          errors={form.formState.errors}
        />
        <CheckedFormInput
          control={form.control}
          name="username"
          placeholder="Username"
          errors={form.formState.errors}
        />
        <div className="space-y-2">
          <CheckedFormInput
            control={form.control}
            name="password"
            placeholder="Password"
            type="password"
            errors={form.formState.errors}
            isPassword={true}
          />
        </div>
        <CheckedFormInput
          control={form.control}
          name="confirmPassword"
          placeholder="Confirm Password"
          type="password"
          errors={form.formState.errors}
          isPassword={true}
        />
        <Button
          type="submit"
          disabled={!form.formState.isValid || form.formState.isSubmitting}
          className="h-10 sm:h-11 text-sm sm:text-base transition-all duration-300 ease-in-out transform hover:scale-105 disabled:scale-100 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
        >
          {form.formState.isSubmitting ? "Creating Account..." : "Register"}
        </Button>
      </form>
    </Form>
  );
};

export default RegisterForm;
