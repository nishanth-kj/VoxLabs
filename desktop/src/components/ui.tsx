"use client";

import { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";
import { IconSpinner, IconX } from "./icons";

export function cn(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

export function Page({
  children,
  className = "",
  width = "default",
}: {
  children: ReactNode;
  className?: string;
  width?: "default" | "narrow";
}) {
  return (
    <div className={cn("min-h-0 w-full flex-1 overflow-y-auto", className)}>
      <div
        className={cn(
          "mx-auto flex w-full flex-col gap-6 px-6 py-6 min-[1100px]:px-8 min-[1100px]:py-7",
          width === "narrow" ? "max-w-2xl" : "max-w-[1120px]",
        )}
      >
        {children}
      </div>
    </div>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("glass rounded-2xl border border-border p-5", className)}>
      {children}
    </div>
  );
}

export function Kicker({ children }: { children: ReactNode }) {
  return (
    <p className="mb-1.5 text-[11px] font-medium uppercase tracking-[0.18em] text-foreground-dim">{children}</p>
  );
}

export function SectionHeader({
  kicker,
  title,
  subtitle,
  actions,
}: {
  kicker?: string;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0">
        {kicker && <Kicker>{kicker}</Kicker>}
        <h1 className="text-[26px] font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1.5 max-w-2xl text-sm leading-relaxed text-foreground-dim">{subtitle}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}

type ButtonVariant = "default" | "primary" | "danger" | "ghost";
type ButtonSize = "sm" | "md";

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  default: "bg-surface-alt border border-border text-foreground hover:border-accent/30 hover:bg-background",
  primary:
    "bg-accent text-white hover:bg-accent-hover border border-transparent shadow-[0_0_20px_rgba(99,102,241,0.28)]",
  danger: "bg-transparent border border-danger/40 text-danger hover:bg-danger/10",
  ghost: "bg-transparent border border-transparent text-foreground-dim hover:bg-surface-alt hover:text-foreground",
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-xs",
  md: "h-9 px-3.5 text-sm",
};

export function buttonStyles(variant: ButtonVariant = "default", size: ButtonSize = "md", className = "") {
  return cn(
    "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
    VARIANT_CLASSES[variant],
    SIZE_CLASSES[size],
    className,
  );
}

export function Button({
  variant = "default",
  size = "md",
  className = "",
  disabled,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant; size?: ButtonSize }) {
  return (
    <button disabled={disabled} className={buttonStyles(variant, size, className)} {...props}>
      {children}
    </button>
  );
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  const { className, ...rest } = props;
  return (
    <input
      {...rest}
      className={cn(
        "h-9 w-full rounded-lg border border-border bg-surface-alt px-3 text-sm outline-none transition-colors placeholder:text-foreground-dim/70 focus:border-accent focus:ring-2 focus:ring-ring",
        className,
      )}
    />
  );
}

export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const { className, ...rest } = props;
  return (
    <textarea
      {...rest}
      className={cn(
        "w-full resize-y rounded-lg border border-border bg-surface-alt px-3 py-2.5 text-sm leading-relaxed outline-none transition-colors placeholder:text-foreground-dim/70 focus:border-accent focus:ring-2 focus:ring-ring",
        className,
      )}
    />
  );
}

export function Select({ children, className, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={cn(
        "h-9 w-full rounded-lg border border-border bg-surface-alt px-3 text-sm outline-none transition-colors focus:border-accent focus:ring-2 focus:ring-ring",
        className,
      )}
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
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="text-foreground-dim">{label}</span>
        <span className="font-mono text-xs tabular-nums text-foreground">
          {format ? format(value) : value.toFixed(2)}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ background: `linear-gradient(to right, var(--accent) ${pct}%, #2a2a36 ${pct}%)` }}
      />
    </div>
  );
}

export function Label({ children, htmlFor }: { children: ReactNode; htmlFor?: string }) {
  return (
    <label htmlFor={htmlFor} className="mb-1.5 block text-xs font-medium tracking-wide text-foreground-dim">
      {children}
    </label>
  );
}

export function Badge({
  children,
  tone = "neutral",
  className = "",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "danger" | "accent";
  className?: string;
}) {
  const tones = {
    neutral: "border-border bg-surface-alt text-foreground-dim",
    success: "border-success/20 bg-success/10 text-success",
    danger: "border-danger/20 bg-danger/10 text-danger",
    accent: "border-accent/25 bg-accent-soft text-accent-hover",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Banner({
  tone,
  children,
  onDismiss,
}: {
  tone: "success" | "error" | "info";
  children: ReactNode;
  onDismiss?: () => void;
}) {
  const tones = {
    success: "border-success/25 bg-success/10 text-success",
    error: "border-danger/25 bg-danger/10 text-danger",
    info: "border-accent/25 bg-accent-soft text-accent-hover",
  };
  return (
    <div className={cn("flex items-start justify-between gap-3 rounded-xl border px-3.5 py-2.5 text-sm", tones[tone])}>
      <div className="min-w-0 leading-relaxed">{children}</div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 rounded-md p-0.5 opacity-70 hover:opacity-100"
          aria-label="Dismiss"
        >
          <IconX className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}

export function Segmented<T extends string>({
  value,
  onChange,
  options,
}: {
  value: T;
  onChange: (v: T) => void;
  options: { value: T; label: string; icon?: ReactNode }[];
}) {
  return (
    <div className="inline-flex self-start rounded-lg border border-border bg-surface-alt p-1">
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-colors",
              active ? "bg-surface text-foreground shadow-sm" : "text-foreground-dim hover:text-foreground",
            )}
          >
            {option.icon}
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
      {icon && (
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-border bg-surface-alt text-foreground-dim">
          {icon}
        </div>
      )}
      <p className="text-sm font-medium">{title}</p>
      <p className="mt-1 max-w-sm text-sm text-foreground-dim">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function SpinnerButton({
  busy,
  children,
  disabled,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant; size?: ButtonSize; busy?: boolean }) {
  return (
    <Button disabled={busy || disabled} {...props}>
      {busy && <IconSpinner className="h-4 w-4" />}
      {children}
    </Button>
  );
}

const WAVE = [18, 32, 24, 44, 28, 52, 36, 22, 48, 30, 40, 20, 56, 34, 26, 42, 18, 38, 28, 46, 22, 50, 33, 19];

export function WaveformBars({
  active = false,
  className = "h-16",
}: {
  active?: boolean;
  className?: string;
}) {
  return (
    <div className={cn("flex items-end gap-[3px]", className)} aria-hidden>
      {WAVE.map((h, i) => (
        <div
          key={i}
          className={cn(
            "flex-1 rounded-sm bg-gradient-to-t from-indigo-600 to-violet-400",
            active ? "eq-bar opacity-90" : "opacity-25",
          )}
          style={{
            height: `${h}%`,
            animationDelay: active ? `${i * 45}ms` : undefined,
          }}
        />
      ))}
    </div>
  );
}
