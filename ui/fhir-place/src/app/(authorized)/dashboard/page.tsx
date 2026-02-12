import Link from "next/link";
import { Button } from "@/components/ui/button";
import { getSetupStatus } from "@/actions/setup-wizard/setup-status";
import { getViableSyncTargets } from "@/actions/setup-wizard/getSystemSetup";
import ResourceCountsDisplay from "@/components/dashboard/ResourceCountsDisplay";

export default async function DashboardPage() {
  const [status, syncTargets] = await Promise.all([
    getSetupStatus(),
    getViableSyncTargets(),
  ]);

  if (status.initialSetupComplete) {
    const showBlaze =
      syncTargets.includes("blaze") || syncTargets.includes("both");
    const showMiabis =
      syncTargets.includes("miabis") || syncTargets.includes("both");

    return (
      <main className="flex-1 p-6 h-full">
        <div className="flex flex-col items-center h-full p-8 space-y-8">
          {showBlaze && (
            <div className="w-full">
              <h3 className="text-xl font-semibold mb-4 text-center">
                Standard FHIR Resources
              </h3>
              <ResourceCountsDisplay isMiabisMode={false} />
            </div>
          )}
          {showMiabis && (
            <div className="w-full">
              <h3 className="text-xl font-semibold mb-4 text-center">
                MIABIS on FHIR Resources
              </h3>
              <ResourceCountsDisplay isMiabisMode={true} />
            </div>
          )}
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
