"use client";

import { ReactNode } from "react";

type Props = {
  icon: ReactNode;
  type?: string;
  placeholder?: string;
  value: string;
  onChange: (v: string) => void;
  autoFocus?: boolean;
};

export default function InputWithIcon({
  icon,
  type = "text",
  placeholder,
  value,
  onChange,
  autoFocus,
}: Props) {
  return (
    <div className="relative">
      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 opacity-60">
        {icon}
      </span>
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        autoFocus={autoFocus}
        className="w-full rounded-lg border border-black/10 bg-white/80 pl-10 pr-3 py-2 text-sm outline-none ring-0 focus:border-violet-500"
      />
    </div>
  );
}
