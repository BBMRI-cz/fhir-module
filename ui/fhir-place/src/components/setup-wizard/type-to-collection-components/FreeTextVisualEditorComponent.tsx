import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { EnumMapping } from "@/types/setup-wizard/types";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export type FreeTextVisualEditorComponentProps = {
  mappings: EnumMapping[];
  addMapping: () => void;
  updateMapping: (
    index: number,
    field: keyof EnumMapping,
    value: string
  ) => void;
  removeMapping: (index: number) => void;
  availableCollectionIds?: string[];
};

export default function FreeTextVisualEditorComponent({
  mappings,
  addMapping,
  updateMapping,
  removeMapping,
  availableCollectionIds = [],
}: FreeTextVisualEditorComponentProps) {
  return (
    <div className="flex flex-col h-full">
      <div className="mb-3">
        <p className="text-xs md:text-sm text-gray-600 mb-2">
          Map your sample types to their corresponding collections.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto mb-4 space-y-2 pr-1">
        {mappings.map((mapping, index) => (
          <Card
            key={index} // NOSONAR
            className="p-3 sm:p-4"
          >
            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
              <div className="flex-1">
                <span className="text-xs font-medium text-gray-700 mb-1 block">
                  Sample Type
                </span>
                <Input
                  value={mapping.userValue}
                  onChange={(e) =>
                    updateMapping(index, "userValue", e.target.value)
                  }
                  placeholder="Enter sample type (e.g., 1, 2, C, T, etc.)"
                  className="h-8 sm:h-10 text-xs sm:text-sm"
                />
              </div>

              <div className="flex-1">
                <span className="text-xs font-medium text-gray-700 mb-1 block">
                  Collection ID
                </span>
                {availableCollectionIds.length > 0 ? (
                  <Select
                    value={mapping.apiValue}
                    onValueChange={(value) =>
                      updateMapping(index, "apiValue", value)
                    }
                  >
                    <SelectTrigger className="h-8 sm:h-10 text-xs sm:text-sm">
                      <SelectValue placeholder="Select collection ID" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableCollectionIds.map((id) => (
                        <SelectItem
                          key={id}
                          value={id}
                          className="text-xs sm:text-sm"
                        >
                          {id}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <Input
                    value={mapping.apiValue}
                    onChange={(e) =>
                      updateMapping(index, "apiValue", e.target.value)
                    }
                    placeholder="Enter collection ID (e.g., bbmri-eric:ID:...)"
                    className="h-8 sm:h-10 text-xs sm:text-sm"
                  />
                )}
              </div>

              <div className="flex items-end">
                <Button
                  onClick={() => removeMapping(index)}
                  variant="destructive"
                  size="sm"
                  className="h-8 sm:h-10 w-full sm:w-auto"
                  disabled={mappings.length === 1}
                >
                  <Trash2 className="w-3 h-3 sm:w-4 sm:h-4" />
                  <span className="ml-1 sm:hidden">Remove</span>
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Button
        onClick={addMapping}
        variant="outline"
        className="w-full h-9 sm:h-10 text-xs sm:text-sm flex-shrink-0"
      >
        <Plus className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
        Add Mapping
      </Button>
    </div>
  );
}
