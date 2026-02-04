import React from "react";

import HelpModule from "./help";
import AdminModule from "./admin";

export const moduleRegistry: Record<string, React.ComponentType> = {
  help: HelpModule,
  admin: AdminModule,
};
