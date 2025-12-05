import { Button } from "@/components/ui/button";
import { SetupWizardContext } from "@/context/SetupWizardContext";
import { useBackendStatus } from "@/hooks/useBackendStatus";
import { useContext } from "react";

export default function WizardInitComponent() {
  const { nextStep } = useContext(SetupWizardContext);
  const isBackendOnline = useBackendStatus();

  const isDisabled = isBackendOnline !== true;

  return (
    <div className="flex flex-col flex-1 items-center">
      <Button
        className="mt-4"
        onClick={() => nextStep()}
        disabled={isDisabled}
      >
        <p>{isDisabled ? "Waiting for backend..." : "Get Started"}</p>
      </Button>
      {isDisabled && (
        <p className="mt-3 text-sm text-muted-foreground">
          Waiting for the FHIR module to start up. Please keep this page open.
        </p>
      )}
    </div>
  )
}