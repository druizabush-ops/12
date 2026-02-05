import React from "react";

import HelpModule from "./help";
import AdminModule from "./admin";

// BLOCK 18 registration rule:
// - key must be equal to backend module.path
// - values are only React components
// - no conditions, no logic, no computations
export const moduleRegistry: Record<string, React.ComponentType> = {
  help: HelpModule,
  admin: AdminModule,
};
