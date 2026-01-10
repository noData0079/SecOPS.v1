"use client";

import React, { Fragment } from "react";
import { Dialog, Transition } from "@headlessui/react";
import { XMarkIcon } from "@heroicons/react/24/outline";

type ServiceModalProps = {
    isOpen: boolean;
    closeModal: () => void;
    title: string;
    content: React.ReactNode;
    ctaAction?: () => void;
    ctaLabel?: string;
};

export function ServiceModal({
    isOpen,
    closeModal,
    title,
    content,
    ctaAction,
    ctaLabel = "Contact Sales",
}: ServiceModalProps) {
    return (
        <Transition appear show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-50" onClose={closeModal}>
                <Transition.Child
                    as={Fragment}
                    enter="ease-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-200"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" />
                </Transition.Child>

                <div className="fixed inset-0 overflow-y-auto">
                    <div className="flex min-h-full items-center justify-center p-4 text-center">
                        <Transition.Child
                            as={Fragment}
                            enter="ease-out duration-300"
                            enterFrom="opacity-0 scale-95"
                            enterTo="opacity-100 scale-100"
                            leave="ease-in duration-200"
                            leaveFrom="opacity-100 scale-100"
                            leaveTo="opacity-0 scale-95"
                        >
                            <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 p-6 text-left align-middle shadow-2xl transition-all">
                                <div className="flex items-center justify-between mb-4">
                                    <Dialog.Title
                                        as="h3"
                                        className="text-xl font-semibold leading-6 text-slate-100"
                                    >
                                        {title}
                                    </Dialog.Title>
                                    <button
                                        onClick={closeModal}
                                        className="text-slate-400 hover:text-white transition"
                                    >
                                        <XMarkIcon className="h-6 w-6" />
                                    </button>
                                </div>

                                <div className="mt-2 text-slate-300 text-sm leading-relaxed space-y-4">
                                    {content}
                                </div>

                                <div className="mt-8 flex justify-end gap-3">
                                    <button
                                        onClick={closeModal}
                                        className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 transition"
                                    >
                                        Close
                                    </button>
                                    <button
                                        onClick={ctaAction}
                                        className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 transition shadow-lg shadow-emerald-500/20"
                                    >
                                        {ctaLabel}
                                    </button>
                                </div>
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
}
