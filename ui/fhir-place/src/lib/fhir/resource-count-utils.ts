export interface ResourceCount {
  resourceType: string;
  count: number;
}

export const parseXMLTotal = (xmlText: string): number => {
  try {
    const pattern1 = /<total\s+value="(\d+)"\s*\/>/;
    const pattern2 = /<total[^>]*value="(\d+)"/;

    let match = pattern1.exec(xmlText);
    match ??= pattern2.exec(xmlText);

    if (match?.[1]) {
      return Number.parseInt(match[1], 10);
    }
    return 0;
  } catch (error) {
    console.error("Error parsing XML total:", error);
    return 0;
  }
};
