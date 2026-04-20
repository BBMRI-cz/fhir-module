import { getMappings } from "@/actions/mappings/get-mappings";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { WandSparkles } from "lucide-react";

function EnumMappingTable({
  data,
  emptyMessage = "No entries configured",
}: {
  data: Record<string, string>;
  emptyMessage?: string;
}) {
  const entries = Object.entries(data);

  if (entries.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-2">{emptyMessage}</p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left py-2 pr-4 font-medium text-muted-foreground w-1/2">
              Source Value
            </th>
            <th className="text-left py-2 font-medium text-muted-foreground w-1/2">
              Target Value
            </th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([key, value]) => (
            <tr key={key} className="border-b last:border-0">
              <td className="py-2 pr-4 font-mono">{key}</td>
              <td className="py-2 font-mono text-primary">{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ParsingMapField({
  fieldName,
  value,
}: {
  fieldName: string;
  value: unknown;
}) {
  if (typeof value === "string") {
    return (
      <tr className="border-b last:border-0">
        <td className="py-2 pr-4 font-mono font-medium">{fieldName}</td>
        <td className="py-2 font-mono text-primary break-all">{value}</td>
      </tr>
    );
  }

  if (typeof value === "object" && value !== null && !Array.isArray(value)) {
    const nested = value as Record<string, unknown>;
    return (
      <>
        <tr className="border-b">
          <td
            colSpan={2}
            className="py-2 font-medium text-muted-foreground text-xs uppercase tracking-wide"
          >
            {fieldName}
          </td>
        </tr>
        {Object.entries(nested).map(([k, v]) => (
          <tr key={`${fieldName}.${k}`} className="border-b last:border-0">
            <td className="py-2 pr-4 pl-4 font-mono text-muted-foreground">
              {k}
            </td>
            <td className="py-2 font-mono text-primary break-all">
              {String(v)}
            </td>
          </tr>
        ))}
      </>
    );
  }

  return null;
}

function ParsingMapTable({
  title,
  data,
}: {
  title: string;
  data: Record<string, unknown> | undefined;
}) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div>
        <h4 className="text-sm font-semibold mb-2">{title}</h4>
        <p className="text-sm text-muted-foreground">Not configured</p>
      </div>
    );
  }

  return (
    <div>
      <h4 className="text-sm font-semibold mb-2">{title}</h4>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2 pr-4 font-medium text-muted-foreground w-1/3">
                Field
              </th>
              <th className="text-left py-2 font-medium text-muted-foreground w-2/3">
                Source Path
              </th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data).map(([key, val]) => (
              <ParsingMapField key={key} fieldName={key} value={val} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default async function MappingsPage() {
  const mappings = await getMappings();

  if (!mappings) {
    return (
      <main className="flex-1 p-6 h-full">
        <div className="flex flex-col items-center justify-center h-full space-y-4">
          <h2 className="text-2xl font-semibold">Mappings unavailable</h2>
          <p className="text-center text-muted-foreground max-w-md">
            Could not load mappings. Make sure the backend is running.
          </p>
        </div>
      </main>
    );
  }

  const { parsing_map, blaze_material_mapping, blaze_temperature_mapping, type_to_collection_mapping, miabis_on_fhir, miabis_material_mapping, miabis_temperature_mapping } = mappings;

  const hasNoMappings =
    Object.keys(parsing_map).length === 0 &&
    Object.keys(blaze_material_mapping).length === 0 &&
    Object.keys(blaze_temperature_mapping).length === 0 &&
    Object.keys(type_to_collection_mapping).length === 0;

  if (hasNoMappings) {
    return (
      <main className="flex-1 p-6 h-full">
        <div className="flex flex-col items-center justify-center h-full space-y-4">
          <h2 className="text-2xl font-semibold">No mappings saved yet</h2>
          <p className="text-center text-muted-foreground max-w-md">
            Run the Setup Wizard to configure your field and enum mappings.
          </p>
          <Button asChild>
            <Link href="/setup-wizard">
              <WandSparkles className="mr-2 h-4 w-4" />
              Go to Setup Wizard
            </Link>
          </Button>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 p-6 h-full overflow-y-auto">
      <div className="space-y-6 max-w-5xl">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Mappings</h2>
            <p className="text-muted-foreground">
              Currently saved field and enum mapping configurations
            </p>
          </div>
          <div className="flex items-center gap-2">
            {miabis_on_fhir && <Badge variant="default">MIABIS on FHIR</Badge>}
            <Button asChild variant="outline" size="sm">
              <Link href="/setup-wizard">
                <WandSparkles className="mr-2 h-4 w-4" />
                Edit in Wizard
              </Link>
            </Button>
          </div>
        </div>

        {/* Parsing Map */}
        <Card>
          <CardHeader>
            <CardTitle>Field Mappings</CardTitle>
            <CardDescription>
              How source data fields map to FHIR resource fields
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <ParsingMapTable
              title="Donor Mapping"
              data={parsing_map.donor_map as Record<string, unknown>}
            />
            <ParsingMapTable
              title="Sample Mapping"
              data={parsing_map.sample_map as Record<string, unknown>}
            />
            <ParsingMapTable
              title="Condition Mapping"
              data={parsing_map.condition_map as Record<string, unknown>}
            />
          </CardContent>
        </Card>

        {/* BLAZE Enum Mappings */}
        <Card>
          <CardHeader>
            <CardTitle>BLAZE Enum Mappings</CardTitle>
            <CardDescription>
              Source values translated to FHIR BLAZE terminology
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h4 className="text-sm font-semibold mb-2">Material Type Mapping</h4>
              <EnumMappingTable
                data={blaze_material_mapping}
                emptyMessage="No material type mappings configured"
              />
            </div>
            <div>
              <h4 className="text-sm font-semibold mb-2">Temperature Mapping</h4>
              <EnumMappingTable
                data={blaze_temperature_mapping}
                emptyMessage="No temperature mappings configured"
              />
            </div>
          </CardContent>
        </Card>

        {/* Type to Collection Mapping */}
        <Card>
          <CardHeader>
            <CardTitle>Type to Collection Mapping</CardTitle>
            <CardDescription>
              Sample type values mapped to collection identifiers
            </CardDescription>
          </CardHeader>
          <CardContent>
            <EnumMappingTable
              data={type_to_collection_mapping}
              emptyMessage="No type-to-collection mappings configured"
            />
          </CardContent>
        </Card>

        {/* MIABIS Enum Mappings */}
        {miabis_on_fhir && (
          <Card>
            <CardHeader>
              <CardTitle>MIABIS Enum Mappings</CardTitle>
              <CardDescription>
                Source values translated to MIABIS on FHIR terminology
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="text-sm font-semibold mb-2">Material Type Mapping</h4>
                <EnumMappingTable
                  data={miabis_material_mapping ?? {}}
                  emptyMessage="No MIABIS material type mappings configured"
                />
              </div>
              <div>
                <h4 className="text-sm font-semibold mb-2">Temperature Mapping</h4>
                <EnumMappingTable
                  data={miabis_temperature_mapping ?? {}}
                  emptyMessage="No MIABIS temperature mappings configured"
                />
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </main>
  );
}