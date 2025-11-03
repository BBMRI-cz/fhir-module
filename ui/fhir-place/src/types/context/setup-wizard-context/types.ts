import { DataField } from "@/types/actions/configuration-details/types";
import { SyncTarget, WizardState } from "@/types/setup-wizard/types";
import { Dispatch, SetStateAction } from "react";

export type Step = {
  stepNumber: 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;
  stepName: string;
  stepTitle: string;
  stepDescription: string;
  stepIcon: React.ReactNode;
  onlyForSyncTargets?: SyncTarget[];
};

export type DataFormat = "json" | "csv" | "xml";

export type SetupWizardContextType = {
  dataFolderPath: string;
  setDataFolderPath: (dataFolderPath: string) => Promise<void>;
  dataFiles: string[];
  dataFormat: DataFormat | null;
  setDataFormat: (dataFormat: DataFormat) => void;
  csvSeparator: string;
  setCsvSeparator: (separator: string) => void;
  step: Step;
  nextStep: () => Step | null;
  previousStep: () => Step | null;
  dataFields: DataField[];
  setDataFields: Dispatch<SetStateAction<DataField[]>>;
  wizardState: WizardState;
  setWizardState: Dispatch<SetStateAction<WizardState>>;
};
