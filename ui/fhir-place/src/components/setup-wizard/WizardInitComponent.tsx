import { Button } from "@/components/ui/button";
import { SetupWizardContext } from "@/context/SetupWizardContext";
import { useContext } from "react";

export default function WizardInitComponent() {
  const { nextStep } = useContext(SetupWizardContext);
  return (
    <div className="flex flex-col flex-1 items-center">
      <Button className="mt-4" onClick={() => nextStep()}>
        <p>Get Started</p>
      </Button>
    </div>
  )
}