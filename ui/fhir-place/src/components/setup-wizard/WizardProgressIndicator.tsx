import { SetupWizardContext, Steps } from "@/context/SetupWizardContext";
import { ArrowRight } from "lucide-react";
import { useContext, Fragment, useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";

export default function WizardProgressIndicator() {
  const { step: currentStep, wizardState } = useContext(SetupWizardContext);

  const visibleSteps = useMemo(() => {
    return Steps.filter((step) => {
      if (step.onlyForSyncTargets) {
        return step.onlyForSyncTargets.includes(wizardState.syncTarget);
      }
      return true;
    });
  }, [wizardState.syncTarget]);

  return (
    <div className="flex flex-col gap-2">
      {/* Progress Indicator - Horizontal for medium+ screens */}
      <div className="hidden 2xl:flex items-center justify-center flex-wrap gap-x-1.5 gap-y-2 max-w-8xl mx-auto">
        {visibleSteps.map((step, index) => {
          let stepIndicatorClass: string;

          if (step.stepNumber > currentStep.stepNumber) {
            stepIndicatorClass = "border-2 border-gray-300";
          } else if (step.stepNumber < currentStep.stepNumber) {
            stepIndicatorClass =
              "border-2 border-green-500 bg-green-500 text-white";
          } else {
            stepIndicatorClass = "bg-blue-500 text-white";
          }

          return (
            <Fragment key={step.stepNumber}>
              <div className="flex items-center space-x-0.5 transition-all duration-300">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium transition-all duration-300 ease-in-out flex-shrink-0 ${stepIndicatorClass}`}
                >
                  {index + 1}
                </div>
                <span className="text-xs font-medium whitespace-nowrap px-1">
                  {step.stepTitle}
                </span>
              </div>
              {index < visibleSteps.length - 1 && (
                <ArrowRight className="w-3 h-3 text-gray-400 flex-shrink-0" />
              )}
            </Fragment>
          );
        })}
      </div>

      {/* Progress Indicator - Current step card for small screens */}
      <div className="2xl:hidden w-full md:w-1/2 mx-auto">
        <Card className="border-blue-500 border-2 py-3 xl:py-3">
          <CardContent className="flex items-center justify-center px-2">
            <div className="flex items-center space-x-1.5">
              <div className="w-6 xl:w-8 h-6 xl:h-8 rounded-full flex items-center justify-center text-md font-medium flex-shrink-0 bg-blue-500">
                {visibleSteps.findIndex(
                  (step) => step.stepNumber === currentStep.stepNumber
                ) + 1}
              </div>
              <span className="text-sm xl:text-md font-medium leading-tight">
                {currentStep.stepTitle}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
