"use client";
import {
  CircleCheckBig,
  FileCheck,
  FolderOpen,
  FolderSync,
  GitBranch,
  HeartHandshake,
  Upload,
} from "lucide-react";
import {
  createContext,
  useState,
  ReactNode,
  useCallback,
  useMemo,
} from "react";
import { getFolders } from "@/actions/folder/list-directories";
import { parseDataFromFolder } from "@/actions/configuration-details/configuration-details-actions";
import { DataField } from "@/types/actions/configuration-details/types";
import {
  Step,
  DataFormat,
  SetupWizardContextType,
} from "@/types/context/setup-wizard-context/types";
import { WizardState } from "@/types/setup-wizard/types";
import {
  getEmptySharedMappings,
  getEmptySyncConfig,
} from "@/lib/setup-wizard/wizard-utils";

export const Steps = [
  {
    stepNumber: 0,
    stepName: "Welcome to Setup Wizard",
    stepTitle: "Welcome",
    stepDescription:
      "Welcome to the Setup Wizard. This is the first step of the setup for the data upload. Click the button below to start.",
    stepIcon: <HeartHandshake className="w-full h-full" />,
  },
  {
    stepNumber: 1,
    stepName: "Select Sync Targets",
    stepTitle: "Select Sync Targets",
    stepDescription:
      "Choose which FHIR servers to sync your data to (BLAZE, MIABIS, or both).",
    stepIcon: <GitBranch className="w-full h-full" />,
  },
  {
    stepNumber: 2,
    stepName: "Select Data Folder & Format",
    stepTitle: "Select Data Folder & Format",
    stepDescription:
      "Select the data folder and specify the format of your data files.",
    stepIcon: <FolderOpen className="w-full h-full" />,
  },
  {
    stepNumber: 3,
    stepName: "Configure BLAZE Enums",
    stepTitle: "Configure BLAZE Enums",
    stepDescription:
      "Configure enum mappings for BLAZE (temperature & material).",
    stepIcon: <Upload className="w-full h-full" />,
    onlyForSyncTargets: ["blaze", "both"],
  },
  {
    stepNumber: 4,
    stepName: "Configure MIABIS Enums",
    stepTitle: "Configure MIABIS Enums",
    stepDescription:
      "Configure enum mappings for MIABIS (temperature & material).",
    stepIcon: <Upload className="w-full h-full" />,
    onlyForSyncTargets: ["miabis", "both"],
  },
  {
    stepNumber: 5,
    stepName: "Configure Mappings",
    stepTitle: "Configure Mappings",
    stepDescription: "Configure data mappings for your FHIR server.",
    stepIcon: <Upload className="w-full h-full" />,
  },
  {
    stepNumber: 6,
    stepName: "Validate Mappings",
    stepTitle: "Validate Mappings",
    stepDescription: "Validate the mappings for selected sync targets.",
    stepIcon: <CircleCheckBig className="w-full h-full" />,
  },
  {
    stepNumber: 7,
    stepName: "Start the sync process",
    stepTitle: "Start the sync process",
    stepDescription: "Start the synchronization process for the data.",
    stepIcon: <FolderSync className="w-full h-full" />,
  },
  {
    stepNumber: 8,
    stepName: "Setup Complete",
    stepTitle: "Setup Complete",
    stepDescription: "The setup process is complete.",
    stepIcon: <FileCheck className="w-full h-full" />,
  },
] as Step[];

function isDataFormat(value: string): value is DataFormat {
  return typeof value === "string" && ["json", "csv", "xml"].includes(value);
}

export const DataFormats: {
  value: DataFormat;
  label: string;
  description: string;
}[] = [
  {
    value: "json",
    label: "JSON",
    description: "JavaScript Object Notation files (.json)",
  },
  {
    value: "csv",
    label: "CSV",
    description: "Comma-Separated Values files (.csv)",
  },
  {
    value: "xml",
    label: "XML",
    description: "eXtensible Markup Language files (.xml)",
  },
];

const defaultValue: SetupWizardContextType = {
  dataFolderPath: "",
  setDataFolderPath: () => Promise.resolve(),
  dataFiles: [],
  dataFormat: null,
  setDataFormat: () => {},
  csvSeparator: ",",
  setCsvSeparator: () => {},
  step: Steps[0],
  nextStep: () => Steps[0],
  previousStep: () => Steps[0],
  dataFields: [],
  setDataFields: () => {},
  wizardState: {
    ...getEmptyWizardState(),
  },
  setWizardState: () => {},
};

function getEmptyWizardState(): WizardState {
  return {
    syncTarget: "blaze",
    sharedMappings: getEmptySharedMappings(),
    blazeConfig: getEmptySyncConfig(),
    miabisConfig: getEmptySyncConfig(),
  };
}

export const SetupWizardContext =
  createContext<SetupWizardContextType>(defaultValue);

export function SetupWizardContextProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [dataFolderPath, setDataFolderPath] = useState<string>("");
  const [dataFiles, setDataFiles] = useState<string[]>([]);
  const [dataFormat, setDataFormat] = useState<DataFormat | null>(null);
  const [csvSeparator, setCsvSeparator] = useState<string>(",");
  const [step, setStep] = useState<Step>(Steps[0]);
  const [dataFields, setDataFields] = useState<DataField[]>([]);

  const [wizardState, setWizardState] = useState<WizardState>({
    ...getEmptyWizardState(),
  });

  const resetConfiguration = useCallback(() => {
    setWizardState((prev) => ({
      ...getEmptyWizardState(),
      syncTarget: prev.syncTarget,
    }));

    setDataFields([]);
  }, []);

  const setCsvSeparatorExtended = useCallback(
    (separator: string) => {
      setCsvSeparator(separator);

      resetConfiguration();

      if (dataFolderPath && dataFormat === "csv") {
        parseDataFromFolder(dataFolderPath, separator).then((result) => {
          if (result.success && result.fields) {
            setDataFields(result.fields);
          }
        });
      }
    },
    [dataFolderPath, dataFormat, resetConfiguration]
  );

  const nextStep = useCallback((): Step | null => {
    if (step.stepNumber === Steps.length) {
      return null;
    }

    const syncTarget = wizardState.syncTarget;

    let nextStep = Steps[step.stepNumber + 1];

    while (
      nextStep?.onlyForSyncTargets &&
      !nextStep.onlyForSyncTargets.includes(syncTarget)
    ) {
      nextStep = Steps[nextStep.stepNumber + 1];
    }

    setStep(nextStep);
    return nextStep;
  }, [step, wizardState.syncTarget]);

  const previousStep = useCallback((): Step | null => {
    if (step.stepNumber === 1) {
      return null;
    }

    const syncTarget = wizardState.syncTarget;
    let previousStep = Steps[step.stepNumber - 1];
    while (
      previousStep?.onlyForSyncTargets &&
      !previousStep.onlyForSyncTargets.includes(syncTarget)
    ) {
      previousStep = Steps[previousStep.stepNumber - 1];
    }

    setStep(previousStep);
    return previousStep;
  }, [step, wizardState.syncTarget]);

  const setDataFolderPathExtended = useCallback(
    async (dataFolderPath: string) => {
      const folder = await getFolders(dataFolderPath, true);
      const files = folder
        .filter((f) => f.isDirectory === false)
        .map((f) => f.name);

      const fileTypeMap = files.reduce((acc, file) => {
        const extension = file.split(".").pop();
        if (extension && isDataFormat(extension)) {
          acc[extension] = (acc[extension] || 0) + 1;
        }
        return acc;
      }, {} as Record<DataFormat, number>);

      let detectedFormat: DataFormat | null = null;
      if (Object.keys(fileTypeMap).length === 1) {
        detectedFormat = Object.keys(fileTypeMap)[0] as DataFormat;
        setDataFormat(detectedFormat);
        setDataFiles(
          files.filter((f) => f.split(".").pop() === detectedFormat)
        );
      } else {
        setDataFiles([]);
      }

      setDataFolderPath(dataFolderPath);

      resetConfiguration();

      if (detectedFormat) {
        parseDataFromFolder(dataFolderPath).then((result) => {
          if (result.success && result.fields) {
            setDataFields(result.fields);
          }
        });
      }
    },
    [resetConfiguration]
  );

  const setDataFormatExtended = useCallback(
    (format: DataFormat) => {
      setDataFormat(format);

      if (dataFolderPath) {
        getFolders(dataFolderPath, true).then((folder) => {
          const files = folder
            .filter((f) => f.isDirectory === false)
            .map((f) => f.name);
          const filteredFiles = files.filter(
            (f) => f.split(".").pop() === format
          );
          setDataFiles(filteredFiles);
        });

        const separator = format === "csv" ? csvSeparator : undefined;
        parseDataFromFolder(dataFolderPath, separator).then((result) => {
          if (result.success && result.fields) {
            setDataFields(result.fields);
          }
        });
      }

      resetConfiguration();
    },
    [dataFolderPath, csvSeparator, resetConfiguration]
  );

  const contextValue = useMemo(
    () => ({
      dataFolderPath,
      setDataFolderPath: setDataFolderPathExtended,
      dataFormat,
      setDataFormat: setDataFormatExtended,
      csvSeparator,
      setCsvSeparator: setCsvSeparatorExtended,
      dataFiles,
      step,
      nextStep,
      previousStep,
      dataFields,
      setDataFields,
      wizardState,
      setWizardState,
    }),
    [
      dataFolderPath,
      setDataFolderPathExtended,
      dataFormat,
      setDataFormatExtended,
      csvSeparator,
      setCsvSeparatorExtended,
      dataFiles,
      step,
      nextStep,
      previousStep,
      dataFields,
      wizardState,
    ]
  );

  return (
    <SetupWizardContext.Provider value={contextValue}>
      {children}
    </SetupWizardContext.Provider>
  );
}
