"use client";

import RegisterForm from "../login/form/RegisterForm";
import Link from "next/link";

export default function Register() {
  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-4 sm:p-8 pb-20 gap-8 sm:gap-16 font-[family-name:var(--font-roboto)]">
      <div className="flex flex-col row-start-2 items-center w-full max-w-sm sm:max-w-md px-4">
        <h1 className="text-2xl sm:text-3xl md:text-6xl font-bold ml-1 text-center">
          Register
        </h1>
        <RegisterForm />
        <div className="mt-4 text-center">
          <p className="text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
