import { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-[10px] border border-border bg-surface p-5 ${className}`}>
      {children}
    </div>
  );
}

export function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-1">
      <h1 className="text-xl font-semibold">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-foreground-dim">{subtitle}</p>}
    </div>
  );
}

type ButtonVariant = "default" | "primary" | "danger";

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  default: "bg-surface-alt border border-border hover:bg-[#2b2b32] active:bg-[#17171a]",
  primary: "bg-accent hover:bg-accent-hover font-semibold border border-transparent",
  danger: "bg-transparent border border-danger text-danger hover:bg-danger/10",
};

export function Button({
  variant = "default",
  className = "",
  disabled,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return (
    <button
      disabled={disabled}
      className={`rounded-md px-4 py-2 text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${VARIANT_CLASSES[variant]} ${className}`}
      {...props}
    />
  );
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`w-full rounded-md border border-border bg-surface-alt px-3 py-2 text-sm outline-none focus:border-accent ${props.className || ""}`}
    />
  );
}

export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={`w-full rounded-md border border-border bg-surface-alt px-3 py-2 text-sm outline-none focus:border-accent ${props.className || ""}`}
    />
  );
}

export function Select({ children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={`w-full rounded-md border border-border bg-surface-alt px-3 py-2 text-sm outline-none focus:border-accent ${props.className || ""}`}
    >
      {children}
    </select>
  );
}

export function Slider({
  label,
  value,
  onChange,
  min,
  max,
  step = 0.01,
  format,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step?: number;
  format?: (v: number) => string;
}) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span>{label}</span>
        <span className="text-foreground-dim">{format ? format(value) : value.toFixed(2)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-[#6d5dfc]"
      />
    </div>
  );
}

export function Label({ children }: { children: ReactNode }) {
  return <label className="mb-1.5 block text-sm text-foreground-dim">{children}</label>;
}
