"use client";

import { SetupWizardContextProvider, SetupWizardContext } from "@/context/SetupWizardContext";
import WizardProgressIndicator from "@/components/setup-wizard/WizardProgressIndicator";
import WizardStepHeader from "@/components/setup-wizard/WizardStepHeader";
import { useContext } from "react";

function WizardLayoutContent({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const { step } = useContext(SetupWizardContext);

  return (
    <div className="p-4 h-full flex flex-col overflow-hidden">
      <div className="flex-shrink-0 2xl:p-2 p-4 flex flex-col gap-2">
        <WizardStepHeader step={step} />
        <div className="py-2">
          <WizardProgressIndicator />
        </div>
      </div>
      <div className="flex-1 overflow-y-auto min-h-0">{children}</div>
    </div>
  );
}

export default function WizardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <SetupWizardContextProvider>
      <WizardLayoutContent>{children}</WizardLayoutContent>
    </SetupWizardContextProvider>
  );
}