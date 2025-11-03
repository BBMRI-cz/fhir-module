"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { ForcePasswordChangeDialog } from "@/components/auth/ForcePasswordChangeDialog";

export const PasswordChangeWrapper = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const { data: session, status } = useSession();
  const [showDialog, setShowDialog] = useState(false);

  useEffect(() => {
    if (status === "authenticated" && session?.user?.mustChangePassword) {
      setShowDialog(true);
    }
  }, [session, status]);

  return (
    <>
      {children}
      <ForcePasswordChangeDialog
        open={showDialog}
        onOpenChange={setShowDialog}
      />
    </>
  );
};
