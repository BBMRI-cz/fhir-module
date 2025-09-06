"use client";

import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useSession } from "next-auth/react";
import { UserDetails } from "@/lib/auth-utils";

export const ProfileOverview = () => {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Profile Overview</CardTitle>
          <CardDescription>Loading...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (!session?.user) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Profile Overview</CardTitle>
          <CardDescription>Please log in to view your profile.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const user = session.user as UserDetails;
  const displayName =
    user.firstName && user.lastName
      ? `${user.firstName} ${user.lastName}`
      : user.username;
  const initials =
    user.firstName && user.lastName
      ? `${user.firstName[0]}${user.lastName[0]}`
      : user.username.slice(0, 2).toUpperCase();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profile Overview</CardTitle>
        <CardDescription>A summary of your account information</CardDescription>
      </CardHeader>
      <div className="px-4">
        <div className="flex items-center space-x-4">
          {/* Avatar circle with gradient */}
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-xl font-medium text-white">
            {initials}
          </div>

          {/* Profile details as simple text */}
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold">{displayName}</h3>
              <Badge variant="secondary" className="text-xs">
                Active
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">@{user.username}</p>

            {user.email && (
              <p className="text-sm text-muted-foreground">{user.email}</p>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};
