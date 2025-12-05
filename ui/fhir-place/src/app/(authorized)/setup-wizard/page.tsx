"use client";

import { useContext } from "react";
import dynamic from "next/dynamic";
import { SetupWizardContext } from "@/context/SetupWizardContext";
import WizardDefineEnumGroupMappingComponent from "@/components/setup-wizard/WizardDefineEnumGroupMappingComponent";

const WizardInitComponent = dynamic(
  () => import("@/components/setup-wizard/WizardInitComponent")
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
      {step.stepNumber === 1 && <WizardSelectSyncTargetsComponent />}
      {step.stepNumber === 2 && <WizardSelectDataFolderComponent />}
      {step.stepNumber === 3 && (
        <WizardDefineEnumGroupMappingComponent targetConfig="blazeConfig" />
      )}
      {step.stepNumber === 4 && (
        <WizardDefineEnumGroupMappingComponent targetConfig="miabisConfig" />
      )}
      {step.stepNumber === 5 && <WizardDefineMappingComponent />}
      {step.stepNumber === 6 && <WizardValidateMappingComponent />}
      {step.stepNumber === 7 && <WizardTriggerSync />}
      {step.stepNumber === 8 && <WizardCompleteComponent />}
    </>
  );
}
