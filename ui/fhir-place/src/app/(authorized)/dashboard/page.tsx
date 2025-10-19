"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { getSetupStatus } from "@/actions/setup-wizard/setup-status";
import { getMode } from "@/actions/backend/get-mode";
import ResourceCountsDisplay from "@/components/dashboard/ResourceCountsDisplay";

export default function DashboardPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [isSetupComplete, setIsSetupComplete] = useState(false);
  const [isMiabisMode, setIsMiabisMode] = useState(false);

  useEffect(() => {
    const checkSetupStatus = async () => {
      const [status, modeResult] = await Promise.all([
        getSetupStatus(),
        getMode(),
      ]);

      setIsSetupComplete(status.initialSetupComplete);
      setIsMiabisMode(modeResult.isMiabisMode);
      setIsLoading(false);
    };

    checkSetupStatus();
  }, []);

  if (isLoading) {
    return (
      <main className="flex-1 p-6 h-full">
        <div className="flex flex-col items-center justify-center h-full">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      </main>
    );
  }

  if (isSetupComplete) {
    return (
      <main className="flex-1 p-6 h-full">
        <div className="flex flex-col items-center h-full p-8">
          <ResourceCountsDisplay isMiabisMode={isMiabisMode} />
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 p-6 h-full">
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <h2 className="text-2xl font-semibold">Welcome to FHIR Module</h2>
        <p className="text-center max-w-md">
          Get started by configuring your FHIR module settings through the setup
          wizard.
        </p>
        <Button asChild>
          <Link href="/setup-wizard">Go to Setup Wizard</Link>
        </Button>
      </div>
    </main>
  );
}
