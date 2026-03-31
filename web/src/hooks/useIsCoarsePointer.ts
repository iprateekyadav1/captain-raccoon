"use client";

import * as React from "react";

export function useIsCoarsePointer() {
  const [isCoarsePointer, setIsCoarsePointer] = React.useState(false);

  React.useEffect(() => {
    const media = window.matchMedia("(pointer: coarse)");
    const update = () => setIsCoarsePointer(media.matches);

    update();
    if (typeof media.addEventListener === "function") {
      media.addEventListener("change", update);
      return () => media.removeEventListener("change", update);
    }

    media.addListener(update);
    return () => media.removeListener(update);
  }, []);

  return isCoarsePointer;
}
