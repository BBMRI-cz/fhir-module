"use client";

import { useForm } from "react-hook-form";
import { LoginFormSchema } from "./schema";
import z from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Form } from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { CheckedFormInput } from "@/components/custom/form/CheckedFormInput";
import { useRouter } from "next/navigation";
import { signIn } from "next-auth/react";

const LoginForm = () => {
  const router = useRouter();
  const form = useForm<z.infer<typeof LoginFormSchema>>({
    resolver: zodResolver(LoginFormSchema),
    defaultValues: {
      username: "",
      password: "",
    },
    mode: "onChange",
  });

  async function onSubmit(data: z.infer<typeof LoginFormSchema>) {
    try {
      const result = await signIn("credentials", {
        username: data.username,
        password: data.password,
        redirect: false,
      });

      if (result?.error) {
        toast.error("Login Failed", {
          description: "Invalid username or password",
        });
      } else {
        router.push("/dashboard");
      }
    } catch (error) {
      toast.error("Login Failed", {
        description: "An unexpected error occurred. Please try again.",
      });
      console.error("Login error:", error);
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
          name="username"
          placeholder="Username"
          errors={form.formState.errors}
        />
        <CheckedFormInput
          control={form.control}
          name="password"
          placeholder="Password"
          type="password"
          errors={form.formState.errors}
        />
        <Button
          type="submit"
          disabled={!form.formState.isValid || form.formState.isSubmitting}
          className="h-10 sm:h-11 text-sm sm:text-base transition-all duration-300 ease-in-out transform hover:scale-105 disabled:scale-100 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
        >
          {form.formState.isSubmitting ? "Logging in..." : "Login"}
        </Button>
      </form>
    </Form>
  );
};

export default LoginForm;
