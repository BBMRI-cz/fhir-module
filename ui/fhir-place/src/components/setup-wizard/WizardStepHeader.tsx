import { Step } from "@/types/context/setup-wizard-context/types";

export default function WizardStepHeader({ step }: { step: Step }) {
  return (
    <div className="text-center space-y-2">
      <div className="flex justify-center mb-2">
        <div className="rounded-full">
          <div className="w-8 h-8">{step.stepIcon}</div>
        </div>
      </div>
      <h1 className="text-2xl font-bold">{step.stepName}</h1>
      <p className="text-md max-w-2xl mx-auto">{step.stepDescription}</p>
    </div>
  );
}

