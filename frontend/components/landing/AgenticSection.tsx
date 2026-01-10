"use client";

import { Disclosure, Transition } from "@headlessui/react";
import { ChevronUpIcon } from "@heroicons/react/24/outline";

export function AgenticSection() {
    return (
        <section className="bg-slate-950 py-16 border-b border-white/5">
            <div className="mx-auto max-w-4xl px-6">
                <div className="rounded-2xl border border-emerald-500/30 bg-emerald-900/10 p-2">
                    <Disclosure>
                        {({ open }) => (
                            <>
                                <Disclosure.Button className="flex w-full items-center justify-between rounded-xl bg-slate-900 px-8 py-6 text-left text-xl font-medium text-emerald-400 hover:bg-slate-800 focus:outline-none focus-visible:ring focus-visible:ring-emerald-500/75 transition-all">
                                    <span>Agentic Reasoning Engine</span>
                                    <ChevronUpIcon
                                        className={`${open ? "rotate-180 transform" : ""
                                            } h-6 w-6 text-emerald-500 transition-transform duration-300`}
                                    />
                                </Disclosure.Button>

                                <Transition
                                    enter="transition duration-100 ease-out"
                                    enterFrom="transform scale-95 opacity-0"
                                    enterTo="transform scale-100 opacity-100"
                                    leave="transition duration-75 ease-out"
                                    leaveFrom="transform scale-100 opacity-100"
                                    leaveTo="transform scale-95 opacity-0"
                                >
                                    <Disclosure.Panel className="px-8 py-6 text-slate-300">
                                        <div className="grid gap-6 md:grid-cols-2">
                                            <ul className="space-y-3">
                                                <li className="flex items-center gap-2">
                                                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                                                    Continuous reasoning
                                                </li>
                                                <li className="flex items-center gap-2">
                                                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                                                    Cross-tool memory
                                                </li>
                                                <li className="flex items-center gap-2">
                                                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                                                    Context-aware decision making
                                                </li>
                                                <li className="flex items-center gap-2">
                                                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                                                    Machine-speed execution
                                                </li>
                                            </ul>
                                            <div className="rounded-lg bg-slate-950/50 p-4 border border-slate-800">
                                                <div className="text-sm font-mono text-emerald-200 mb-2">Flow:</div>
                                                <div className="flex items-center gap-2 text-xs text-slate-400">
                                                    <span>Detect</span>
                                                    <span>→</span>
                                                    <span>Explain</span>
                                                    <span>→</span>
                                                    <span>Fix</span>
                                                </div>
                                                <div className="mt-3 pt-3 border-t border-slate-800 text-xs text-slate-500 italic">
                                                    "One-click commit for DevOps teams"
                                                </div>
                                            </div>
                                        </div>
                                    </Disclosure.Panel>
                                </Transition>
                            </>
                        )}
                    </Disclosure>
                </div>
            </div>
        </section>
    );
}
