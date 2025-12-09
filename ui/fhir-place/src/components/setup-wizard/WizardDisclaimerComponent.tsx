"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { SetupWizardContext } from "@/context/SetupWizardContext";
import { AlertTriangle, BookOpen, Info } from "lucide-react";
import { useContext } from "react";

export default function WizardDisclaimerComponent() {
  const { nextStep, previousStep } = useContext(SetupWizardContext);

  return (
    <div className="h-full w-full bg-gradient-to-br">
      <Card className="border-0 shadow-xl h-full w-full flex flex-col">
        <CardHeader className="flex-shrink-0">
          <CardTitle className="text-base lg:text-2xl font-semibold flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 lg:h-6 lg:w-6 text-amber-500" />
            Before You Begin
          </CardTitle>
          <p className="text-muted-foreground text-xs sm:text-sm leading-tight sm:leading-normal">
            Please read the following important information before proceeding
            with the setup.
          </p>
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto space-y-4">
          {/* Best Effort Notice */}
          <div className="rounded-lg border bg-muted/30 p-4">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="text-sm font-semibold">Best Effort Service</h4>
                <p className="text-sm text-muted-foreground">
                  This wizard provides a <strong>best effort</strong> approach
                  to configure the FHIR module. While we aim to help you as much
                  as possible, some manual configuration may be required
                  depending on your data structure.
                </p>
              </div>
            </div>
          </div>

          {/* Requirements Section */}
          <div className="rounded-lg border bg-muted/30 p-4">
            <div className="flex items-start gap-3">
              <BookOpen className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="text-sm font-semibold text-amber-500">
                  Knowledge Required
                </h4>
                <p className="text-sm text-muted-foreground">
                  You will need some understanding of your{" "}
                  <strong>data structure</strong> and the{" "}
                  <strong>existing values</strong> in your files to properly
                  configure the mappings and enumerations.
                </p>
              </div>
            </div>
          </div>

          {/* Limitations Section */}
          <div className="rounded-lg border bg-muted/30 p-4 space-y-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              <h4 className="text-sm font-semibold text-orange-500">
                Important Limitations
              </h4>
            </div>

            <p className="text-sm text-muted-foreground ml-7">
              To keep the performance and as processing all the files during setup might be impossible
              automatic operations such as validation and automatic enum inference
              process <strong>up to 1000 files</strong> from the selected
              folder. Results may vary depending on how representative this
              sample is of your complete dataset.{" "}
              <span className="font-medium">
                Manual definition of additional values or paths may be required.
              </span>
            </p>
          </div>
        </CardContent>

        <CardFooter className="flex justify-between gap-2 p-4 sm:p-6">
          <Button
            onClick={previousStep}
            variant="outline"
            className="h-8 sm:h-10 text-xs sm:text-sm px-2 sm:px-4"
          >
            Back
          </Button>
          <Button
            onClick={nextStep}
            className="h-8 sm:h-10 text-xs sm:text-sm px-3 sm:px-4"
          >
            I Understand
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}

