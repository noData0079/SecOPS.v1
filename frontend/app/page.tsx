"use client";

import { useRef } from "react";
import { MagneticButton } from "@/components/ui/MagneticButton";
import { useGhostScroll } from "@/hooks/useGhostScroll";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Sphere, MeshDistortMaterial } from "@react-three/drei";

// Simple 3D Placeholder Component
const SovereignOrb = () => {
  return (
    <Sphere args={[1, 100, 200]} scale={2.4}>
      <MeshDistortMaterial
        color="#00FFFF"
        attach="material"
        distort={0.4}
        speed={2}
        roughness={0.2}
        metalness={0.8}
      />
    </Sphere>
  );
};

export default function HomePage() {
  const scrollRef = useRef<HTMLDivElement>(null);
  useGhostScroll(scrollRef, ".axiom-card");

  return (
    <main className="min-h-screen bg-sovereign-black text-white selection:bg-sovereign-cyan selection:text-sovereign-black overflow-x-hidden">
      {/* Hero Section */}
      <section className="relative h-screen w-full flex items-center justify-center border-b border-white/10 overflow-hidden">
        <div className="absolute inset-0 z-0">
           <Canvas className="opacity-60">
             <ambientLight intensity={0.5} />
             <directionalLight position={[10, 10, 5]} intensity={1} />
             <pointLight position={[-10, -10, -10]} color="#FFB800" intensity={2} />
             <SovereignOrb />
             <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.5} />
           </Canvas>
        </div>

        <div className="z-10 text-center space-y-8 p-4 relative pointer-events-none">
          <div className="pointer-events-auto">
            <h1 className="text-6xl md:text-9xl font-black tracking-tighter uppercase font-sans mb-4 mix-blend-difference">
              Sovereign <br/> <span className="text-transparent bg-clip-text bg-gradient-to-r from-sovereign-cyan to-white">Mechanica</span>
            </h1>
            <p className="text-xl md:text-2xl text-gray-400 font-mono max-w-2xl mx-auto mb-8">
              Autonomous Command Center. <span className="text-sovereign-amber">Pure Kinetic Intelligence.</span>
            </p>
            <div className="flex justify-center gap-4">
               <MagneticButton onClick={() => console.log('Deploy')}>
                 Initialize TSM99
               </MagneticButton>
            </div>
          </div>
        </div>
      </section>

      {/* Evolution Lab / Ghost Scroll Section */}
      <section ref={scrollRef} className="py-32 px-4 md:px-12 max-w-7xl mx-auto space-y-32">
        <div className="text-center space-y-4 mb-20">
           <h2 className="text-4xl font-bold uppercase tracking-widest text-sovereign-amber">System Axioms</h2>
           <div className="h-1 w-24 bg-sovereign-amber mx-auto"></div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            { title: "Digital Twin", desc: "Real-time network mirroring with high-fidelity 3D simulation." },
            { title: "Recursive Logic", desc: "Self-healing autonomy loops that rewrite their own axioms." },
            { title: "Hardware Trust", desc: "Ice-Age sovereign security locked to the physical TPM." },
          ].map((item, i) => (
            <div key={i} className="axiom-card p-8 border border-white/10 bg-white/5 backdrop-blur-sm rounded-xl hover:border-sovereign-cyan hover:bg-sovereign-cyan/5 transition-all duration-500 group cursor-crosshair">
              <div className="h-12 w-12 bg-sovereign-cyan/20 rounded-full mb-6 flex items-center justify-center text-sovereign-cyan group-hover:scale-110 transition-transform">
                {/* Icon Placeholder */}
                <span className="font-mono text-xl">0{i+1}</span>
              </div>
              <h3 className="text-2xl font-mono text-sovereign-cyan mb-4 group-hover:text-white transition-colors">{item.title}</h3>
              <p className="text-gray-400 group-hover:text-gray-300 transition-colors">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Recursive Loop Placeholder (Visual requirement) */}
      <section className="h-[50vh] flex flex-col items-center justify-center bg-gradient-to-t from-sovereign-cyan/10 to-transparent relative border-t border-white/5">
         <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20"></div>
         <p className="font-mono text-sovereign-cyan animate-pulse tracking-widest text-lg">RECURSIVE LOOP VISUALIZATION PENDING...</p>
         <div className="mt-8 flex gap-4">
            <div className="w-4 h-4 rounded-full bg-sovereign-amber shadow-[0_0_15px_#FFB800]"></div>
            <div className="w-4 h-4 rounded-full bg-sovereign-cyan shadow-[0_0_15px_#00FFFF]"></div>
            <div className="w-4 h-4 rounded-full bg-sovereign-amber shadow-[0_0_15px_#FFB800]"></div>
         </div>
      </section>
    </main>
  );
}
