"use client";

import { useState, useEffect } from "react";

export function useSidebar() {
  const [open, setOpen] = useState(true);
  useEffect(() => {
    const saved = localStorage.getItem("sidebar_open");
    if (saved) setOpen(saved === "1");
  }, []);
  useEffect(() => {
    localStorage.setItem("sidebar_open", open ? "1" : "0");
  }, [open]);
  return { open, setOpen };
}
