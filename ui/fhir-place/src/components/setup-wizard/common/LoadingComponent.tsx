export default function LoadingComponent() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading data...</p>
      </div>
    </div>
  );
}