import type { MatchType } from "@/types";

export function getMatchTypeLabel(
  type: MatchType
): string {
  switch (type) {
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