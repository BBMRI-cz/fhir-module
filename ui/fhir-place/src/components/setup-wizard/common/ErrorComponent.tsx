import { Button } from "@/components/ui/button";

export default function ErrorComponent({ message }: { message: string }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <h3 className="text-red-800 font-medium mb-2">Error Loading Data</h3>
      <p className="text-red-600 text-sm">{message}</p>
      <Button
        onClick={() => globalThis.location.reload()}
        variant="outline"
        size="sm"
        className="mt-3"
      >
        Retry
      </Button>
    </div>
  );
}
