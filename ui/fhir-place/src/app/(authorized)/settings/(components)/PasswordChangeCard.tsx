"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PasswordChangeForm } from "./PasswordChangeForm";

export const PasswordChangeCard = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Password Security</CardTitle>
        <CardDescription>
          Update your password to keep your account secure.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <PasswordChangeForm />
      </CardContent>
    </Card>
  );
};
