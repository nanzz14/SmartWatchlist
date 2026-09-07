import * as React from "react";
import { cn } from "@/lib/utils";

export type ButtonVariant = "default" | "outline" | "ghost" | "danger";
export type ButtonSize = "default" | "sm" | "lg" | "icon" | "icon-sm";

const variantStyles: Record<ButtonVariant, string> = {
  default: "bg-primary text-primary-fg hover:bg-primary/90",
  outline: "bg-transparent text-fg shadow-[var(--shadow-border)] hover:shadow-[var(--shadow-border-hover)] hover:bg-elevated",
  ghost: "text-muted hover:text-fg hover:bg-elevated",
  danger: "bg-down/15 text-down hover:bg-down/25",
};

const sizeStyles: Record<ButtonSize, string> = {
  default: "h-11 rounded-md px-4",
  sm: "h-9 rounded-sm px-3 text-[13px]",
  lg: "h-12 rounded-md px-5",
  icon: "size-11 rounded-md flex items-center justify-center",
  "icon-sm": "size-9 rounded-sm flex items-center justify-center",
};

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", asChild = false, children, ...props }, ref) => {
    const combinedClasses = cn(
      "inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium transition-[color,background-color,box-shadow,transform,opacity] duration-150 ease-out disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 outline-none focus-visible:ring-2 focus-visible:ring-ring active:not-disabled:scale-[0.96] cursor-pointer",
      variantStyles[variant],
      sizeStyles[size],
      className
    );

    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children as React.ReactElement<any>, {
        className: cn((children.props as any).className, combinedClasses),
        ref,
        ...props,
      });
    }

    return (
      <button ref={ref} className={combinedClasses} {...props}>
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
