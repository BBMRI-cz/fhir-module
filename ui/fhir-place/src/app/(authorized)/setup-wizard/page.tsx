"use client";

import { useContext } from "react";
import dynamic from "next/dynamic";
import { SetupWizardContext } from "@/context/SetupWizardContext";
import WizardDefineEnumGroupMappingComponent from "@/components/setup-wizard/WizardDefineEnumGroupMappingComponent";

const WizardInitComponent = dynamic(
  () => import("@/components/setup-wizard/WizardInitComponent")
);
const WizardDisclaimerComponent = dynamic(
  () => import("@/components/setup-wizard/WizardDisclaimerComponent")
);
const WizardSelectDataFolderComponent = dynamic(
  () => import("@/components/setup-wizard/WizardSelectDataFolderComponent")
);
const WizardSelectSyncTargetsComponent = dynamic(
  () => import("@/components/setup-wizard/WizardSelectSyncTargetsComponent")
);
const WizardDefineMappingComponent = dynamic(
  () => import("@/components/setup-wizard/WizardDefineMappingComponent")
);
const WizardValidateMappingComponent = dynamic(
  () => import("@/components/setup-wizard/WizardValidateMappingComponent")
);
const WizardTriggerSync = dynamic(
  () => import("@/components/setup-wizard/WizardTriggerSync")
);
const WizardCompleteComponent = dynamic(
  () => import("@/components/setup-wizard/WizardCompleteComponent")
);

export default function SetupWizard() {
  const { step } = useContext(SetupWizardContext);

  return (
    <>
      {step.stepNumber === 0 && <WizardInitComponent />}
      {step.stepNumber === 1 && <WizardDisclaimerComponent />}
      {step.stepNumber === 2 && <WizardSelectSyncTargetsComponent />}
      {step.stepNumber === 3 && <WizardSelectDataFolderComponent />}
      {step.stepNumber === 4 && (
        <WizardDefineEnumGroupMappingComponent targetConfig="blazeConfig" />
      )}
      {step.stepNumber === 5 && (
        <WizardDefineEnumGroupMappingComponent targetConfig="miabisConfig" />
      )}
      {step.stepNumber === 6 && <WizardDefineMappingComponent />}
      {step.stepNumber === 7 && <WizardValidateMappingComponent />}
      {step.stepNumber === 8 && <WizardTriggerSync />}
      {step.stepNumber === 9 && <WizardCompleteComponent />}
    </>
  );
}
