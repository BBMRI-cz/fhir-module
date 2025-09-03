"use server";

export interface PrometheusQueryData {
  resultType: string;
  result: Array<{
    metric: Record<string, string>;
    value?: [number, string];
    values?: Array<[number, string]>;
  }>;
}

export interface PrometheusQueryResult {
  success: boolean;
  message: string;
  data?: PrometheusQueryData;
}

export async function queryPrometheusAction(
  query: string
): Promise<PrometheusQueryResult> {
  try {
    if (!query || query.trim() === "") {
      return {
        success: false,
        message: "Query parameter is required",
      };
    }

    const prometheusBaseUrl =
      process.env.PROMETHEUS_URL || "http://prometheus:9090";
    const prometheusUrl = `${prometheusBaseUrl}/api/v1/query`;
    const url = new URL(prometheusUrl);
    url.searchParams.append("query", query);

    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      return {
        success: false,
        message: `Prometheus API request failed: ${response.status} ${response.statusText}`,
      };
    }

    const data = await response.json();

    if (data.status === "error") {
      return {
        success: false,
        message: `Prometheus query error: ${data.error || "Unknown error"}`,
      };
    }

    return {
      success: true,
      message: "Query executed successfully",
      data: data.data,
    };
  } catch (error) {
    console.error("Error querying Prometheus:", error);

    return {
      success: false,
      message:
        error instanceof Error
          ? error.message
          : "An unexpected error occurred while querying Prometheus",
    };
  }
}
