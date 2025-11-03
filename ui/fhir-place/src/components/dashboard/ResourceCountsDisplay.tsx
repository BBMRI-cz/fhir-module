"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Building2,
  Users,
  FileText,
  TestTube,
  Loader2,
  AlertCircle,
} from "lucide-react";
import {
  getResourceCounts,
  getMiabisResourceCounts,
  type ResourceCountsResponse,
} from "@/actions/backend/get-resource-counts";

const RESOURCE_ICONS = {
  Organization: Building2,
  Patient: Users,
  Condition: FileText,
  Specimen: TestTube,
  BiobankOrganization: Building2,
  SampleCollection: Building2,
} as const;

const RESOURCE_LABELS = {
  Organization: "Organizations",
  Patient: "Patients",
  Condition: "Conditions",
  Specimen: "Specimens",
  BiobankOrganization: "Biobank",
  SampleCollection: "Collections",
} as const;

const RESOURCE_ORDER = [
  "Organization",
  "BiobankOrganization",
  "SampleCollection",
  "Patient",
  "Condition",
  "Specimen",
] as const;

interface ResourceCountsDisplayProps {
  isMiabisMode?: boolean;
}

export default function ResourceCountsDisplay({
  isMiabisMode = false,
}: ResourceCountsDisplayProps) {
  const [resourceCounts, setResourceCounts] =
    useState<ResourceCountsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchCounts = async () => {
      setIsLoading(true);
      const counts = isMiabisMode
        ? await getMiabisResourceCounts()
        : await getResourceCounts();
      setResourceCounts(counts);
      setIsLoading(false);
    };

    fetchCounts();
  }, [isMiabisMode]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!resourceCounts?.success || !resourceCounts.resources) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center p-8 space-x-2 text-destructive">
          <AlertCircle className="w-5 h-5" />
          <span>Failed to load resource counts</span>
        </CardContent>
      </Card>
    );
  }

  // Create a map for quick lookup
  const countsMap = resourceCounts.resources.reduce((acc, resource) => {
    acc[resource.resourceType] = resource.count;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="space-y-4 w-full">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold mb-2">Resource Overview</h2>
        <p className="text-muted-foreground">
          Current count of resources in the FHIR server
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {RESOURCE_ORDER.map((resourceType) => {
          const count = countsMap[resourceType];
          if (count === undefined) return null;

          const Icon = RESOURCE_ICONS[resourceType] || FileText;
          const label = RESOURCE_LABELS[resourceType] || resourceType;

          return (
            <Card
              key={resourceType}
              className="hover:shadow-lg transition-shadow"
            >
              <CardHeader className="pb-3">
                <div className="flex items-center space-x-2">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Icon className="w-5 h-5 text-primary" />
                  </div>
                  <CardTitle className="text-base font-medium">
                    {label}
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-primary">
                  {count.toLocaleString()}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {count === 1 ? "record" : "records"}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
