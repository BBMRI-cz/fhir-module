"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { UserDetailsForm } from "@/app/(authorized)/settings/(components)/UserDetailsForm";

export const UserDetailsCard = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Account Settings</CardTitle>
        <CardDescription>Update your account information.</CardDescription>
      </CardHeader>
      <CardContent>
        <UserDetailsForm />
      </CardContent>
    </Card>
  );
};
