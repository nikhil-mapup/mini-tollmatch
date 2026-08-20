import type { Mismatch } from "@/types";

export function getMatchTypeLabel(
  type: Mismatch
): string {
  switch (type.verdict) {
    case "matched":
      return "Matched";

    case "misread":
      return "Misread";

    case "unmatched":
      return "Unmatched";

    case "max_toll":
      return "Max Toll";

    case "unassigned":
      return "Unassigned";

    case "duplicate":
      return "Duplicate";

    // case "insufficient_gps":
    //   return "Insufficient GPS";

    default:
      return "Unknown";
  }
}