"use client";

import React, { useEffect } from "react";
import ReactDOM from "react-dom";
import clsx from "clsx";
import { X } from "lucide-react";

export type ModalSize = "sm" | "md" | "lg" | "xl";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  size?: ModalSize;
  closeOnOverlayClick?: boolean;
  showCloseIcon?: boolean;
  footer?: React.ReactNode;         // e.g. buttons row
  children?: React.ReactNode;
  className?: string;               // extra classes for the inner panel
}

/* -------------------------------------------------------------------------- */
/*                               Size → max-width                             */
/* -------------------------------------------------------------------------- */

const sizeClassMap: Record<ModalSize, string> = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
};

/* -------------------------------------------------------------------------- */
/*                                 Modal Root                                  */
/* -------------------------------------------------------------------------- */

const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  size = "md",
  closeOnOverlayClick = true,
  showCloseIcon = true,
  footer,
  children,
  className,
}) => {
  // Lock body scroll when modal is open
  useEffect(() => {
    if (!isOpen) return;

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleOverlayClick = () => {
    if (closeOnOverlayClick) {
      onClose();
    }
  };

  const modalContent = (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-[1px]"
        onClick={handleOverlayClick}
      />

      {/* Dialog */}
      <div
        className={clsx(
          "relative z-10 w-full mx-4 rounded-xl bg-white shadow-xl border border-neutral-200",
          "max-h-[90vh] flex flex-col",
          sizeClassMap[size],
          className
        )}
      >
        {/* Header */}
        {(title || showCloseIcon) && (
          <div className="flex items-center justify-between px-4 pt-4 pb-2 border-b border-neutral-100">
            <div className="flex flex-col gap-1 pr-2">
              {title && (
                <h2 className="text-base font-semibold text-neutral-900">
                  {title}
                </h2>
              )}
              {description && (
                <p className="text-xs text-neutral-500">{description}</p>
              )}
            </div>
            {showCloseIcon && (
              <button
                type="button"
                onClick={onClose}
                className="p-1 rounded-md text-neutral-500 hover:bg-neutral-100 hover:text-neutral-800 transition-colors"
                aria-label="Close dialog"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        )}

        {/* Body */}
        <div className="px-4 py-3 overflow-y-auto">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="px-4 py-3 border-t border-neutral-100 bg-neutral-50 flex justify-end gap-2">
            {footer}
          </div>
        )}
      </div>
    </div>
  );

  // Use portal if document.body is available
  if (typeof document !== "undefined") {
    return ReactDOM.createPortal(modalContent, document.body);
  }

  return modalContent;
};

export default Modal;
