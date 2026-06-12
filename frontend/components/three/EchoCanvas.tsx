"use client";

import { useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Float } from "@react-three/drei";
import * as THREE from "three";

type VariantLatar = "hero" | "section" | "dashboard" | "submit";

interface EchoCanvasProps {
  variant: VariantLatar;
  aktif?: boolean;
}

interface KonfigurasiJaringan {
  jumlah_node: number;
  jarak_koneksi: number;
  kecepatan_putar: number;
  ukuran_partikel: number;
  max_garis: number;
  mode_gelap: boolean;
  warna_kabut: string;
}

const KONFIGURASI: Record<VariantLatar, KonfigurasiJaringan> = {
  hero: {
    jumlah_node: 110,
    jarak_koneksi: 2.2,
    kecepatan_putar: 0.007,
    ukuran_partikel: 0.075,
    max_garis: 340,
    mode_gelap: true,
    warna_kabut: "#020818",
  },
  section: {
    jumlah_node: 65,
    jarak_koneksi: 1.9,
    kecepatan_putar: 0.006,
    ukuran_partikel: 0.055,
    max_garis: 200,
    mode_gelap: false,
    warna_kabut: "#f8fafc",
  },
  dashboard: {
    jumlah_node: 55,
    jarak_koneksi: 1.8,
    kecepatan_putar: 0.005,
    ukuran_partikel: 0.05,
    max_garis: 160,
    mode_gelap: false,
    warna_kabut: "#f8fafc",
  },
  submit: {
    jumlah_node: 70,
    jarak_koneksi: 2.0,
    kecepatan_putar: 0.007,
    ukuran_partikel: 0.058,
    max_garis: 220,
    mode_gelap: false,
    warna_kabut: "#f8fafc",
  },
};

/* Warna partikel mode gelap — lebih terang dan bercahaya */
const PALET_GELAP = [
  new THREE.Color("#ff6b6b"),
  new THREE.Color("#fbbf24"),
  new THREE.Color("#60a5fa"),
  new THREE.Color("#94a3b8"),
  new THREE.Color("#7c3aed"),
];

/* Warna partikel mode terang */
const PALET_TERANG = [
  new THREE.Color("#ef4444"),
  new THREE.Color("#f59e0b"),
  new THREE.Color("#3b82f6"),
  new THREE.Color("#64748b"),
  new THREE.Color("#0f172a"),
];

function buatDataJaringan(konfig: KonfigurasiJaringan) {
  const { jumlah_node, jarak_koneksi, max_garis, mode_gelap } = konfig;
  const palet = mode_gelap ? PALET_GELAP : PALET_TERANG;
  const posisi_node: THREE.Vector3[] = [];
  const posisi_partikel = new Float32Array(jumlah_node * 3);
  const warna_partikel = new Float32Array(jumlah_node * 3);

  for (let i = 0; i < jumlah_node; i++) {
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    const radius = 2.4 + Math.random() * 2.6;
    const x = radius * Math.sin(phi) * Math.cos(theta);
    const y = radius * Math.sin(phi) * Math.sin(theta) * 0.55;
    const z = radius * Math.cos(phi);
    posisi_node.push(new THREE.Vector3(x, y, z));

    posisi_partikel[i * 3] = x;
    posisi_partikel[i * 3 + 1] = y;
    posisi_partikel[i * 3 + 2] = z;

    const roll = Math.random();
    const indeks = roll < 0.1 ? 0 : roll < 0.2 ? 1 : roll < 0.4 ? 2 : roll < 0.65 ? 3 : 4;
    const warna = palet[indeks];
    warna_partikel[i * 3] = warna.r;
    warna_partikel[i * 3 + 1] = warna.g;
    warna_partikel[i * 3 + 2] = warna.b;
  }

  const posisi_garis: number[] = [];
  const warna_garis: number[] = [];

  for (let i = 0; i < jumlah_node && posisi_garis.length / 6 < max_garis; i++) {
    for (let j = i + 1; j < jumlah_node && posisi_garis.length / 6 < max_garis; j++) {
      const jarak = posisi_node[i].distanceTo(posisi_node[j]);
      if (jarak < jarak_koneksi) {
        posisi_garis.push(
          posisi_node[i].x, posisi_node[i].y, posisi_node[i].z,
          posisi_node[j].x, posisi_node[j].y, posisi_node[j].z,
        );
        const kekuatan = 1 - jarak / jarak_koneksi;
        /* Garis lebih terang di mode gelap */
        const nilai = mode_gelap
          ? 0.18 + kekuatan * 0.35
          : 0.35 + kekuatan * 0.45;
        warna_garis.push(nilai, nilai, mode_gelap ? nilai + 0.12 : nilai + 0.04,
                         nilai, nilai, mode_gelap ? nilai + 0.12 : nilai + 0.04);
      }
    }
  }

  const geo_partikel = new THREE.BufferGeometry();
  geo_partikel.setAttribute("position", new THREE.BufferAttribute(posisi_partikel, 3));
  geo_partikel.setAttribute("color", new THREE.BufferAttribute(warna_partikel, 3));

  const geo_garis = new THREE.BufferGeometry();
  geo_garis.setAttribute("position", new THREE.BufferAttribute(new Float32Array(posisi_garis), 3));
  geo_garis.setAttribute("color", new THREE.BufferAttribute(new Float32Array(warna_garis), 3));

  return { geo_partikel, geo_garis };
}

function ParallaxKamera({ aktif }: { aktif: boolean }) {
  const { camera, pointer } = useThree();
  const target = useRef({ x: 0, y: 0 });

  useFrame(() => {
    if (!aktif) return;
    target.current.x = THREE.MathUtils.lerp(target.current.x, pointer.x * 0.3, 0.035);
    target.current.y = THREE.MathUtils.lerp(target.current.y, pointer.y * 0.18, 0.035);
    camera.position.x = target.current.x;
    camera.position.y = target.current.y;
    camera.lookAt(0, 0, 0);
  });

  return null;
}

function JaringanMemori({ variant, aktif }: { variant: VariantLatar; aktif: boolean }) {
  const grup_ref = useRef<THREE.Group>(null);
  const konfig = KONFIGURASI[variant];
  const { geo_partikel, geo_garis } = useMemo(() => buatDataJaringan(konfig), [variant, konfig]);

  useEffect(() => {
    return () => {
      geo_partikel.dispose();
      geo_garis.dispose();
    };
  }, [geo_partikel, geo_garis]);

  useFrame((state) => {
    if (!grup_ref.current || !aktif) return;
    const t = state.clock.elapsedTime;
    grup_ref.current.rotation.y = t * konfig.kecepatan_putar;
    grup_ref.current.rotation.x = Math.sin(t * 0.11) * 0.03;
    grup_ref.current.position.y = Math.sin(t * 0.18) * 0.05;
  });

  const opasitas_partikel = konfig.mode_gelap ? 0.9 : 0.88;
  const opasitas_garis = konfig.mode_gelap ? 0.35 : 0.20;

  return (
    <Float speed={1.0} rotationIntensity={0.06} floatIntensity={0.12}>
      <group ref={grup_ref}>
        <points geometry={geo_partikel}>
          <pointsMaterial
            size={konfig.ukuran_partikel}
            vertexColors
            transparent
            opacity={opasitas_partikel}
            sizeAttenuation
            depthWrite={false}
            blending={konfig.mode_gelap ? THREE.AdditiveBlending : THREE.NormalBlending}
          />
        </points>

        <lineSegments geometry={geo_garis}>
          <lineBasicMaterial
            vertexColors
            transparent
            opacity={opasitas_garis}
            depthWrite={false}
            blending={konfig.mode_gelap ? THREE.AdditiveBlending : THREE.NormalBlending}
          />
        </lineSegments>

        {/* Cincin orbit */}
        <mesh rotation={[Math.PI / 2.4, 0.3, 0]}>
          <torusGeometry args={[4.5, 0.008, 8, 140]} />
          <meshBasicMaterial
            color={konfig.mode_gelap ? "#334155" : "#94a3b8"}
            transparent
            opacity={konfig.mode_gelap ? 0.25 : 0.12}
          />
        </mesh>
        <mesh rotation={[Math.PI / 3.2, -0.5, 0.8]}>
          <torusGeometry args={[3.2, 0.006, 6, 100]} />
          <meshBasicMaterial
            color={konfig.mode_gelap ? "#1e40af" : "#cbd5e1"}
            transparent
            opacity={konfig.mode_gelap ? 0.2 : 0.10}
          />
        </mesh>
      </group>
    </Float>
  );
}

function Pencahayaan({ variant }: { variant: VariantLatar }) {
  const konfig = KONFIGURASI[variant];
  return (
    <>
      <color attach="background" args={[konfig.warna_kabut]} />
      <fog attach="fog" args={[konfig.warna_kabut, konfig.mode_gelap ? 8 : 7, konfig.mode_gelap ? 20 : 16]} />
      <ambientLight intensity={konfig.mode_gelap ? 0.5 : 0.7} />
      <pointLight position={[5, 4, 6]} intensity={konfig.mode_gelap ? 0.8 : 0.5} color={konfig.mode_gelap ? "#fbbf24" : "#f59e0b"} />
      <pointLight position={[-5, -3, 4]} intensity={konfig.mode_gelap ? 0.6 : 0.35} color={konfig.mode_gelap ? "#60a5fa" : "#3b82f6"} />
      <pointLight position={[0, -4, -3]} intensity={konfig.mode_gelap ? 0.35 : 0.18} color={konfig.mode_gelap ? "#f87171" : "#ef4444"} />
    </>
  );
}

export default function EchoCanvas({ variant, aktif = true }: EchoCanvasProps) {
  const isMobile = typeof window !== "undefined" && window.innerWidth < 768;
  const dpr: [number, number] = isMobile ? [1, 1] : [1, 1.5];
  const antiAlias = !isMobile;

  return (
    <Canvas
      camera={{ position: [0, 0, 8], fov: 50 }}
      dpr={dpr}
      frameloop={aktif ? "always" : "demand"}
      gl={{ antialias: antiAlias, alpha: false, powerPreference: "high-performance" }}
      style={{ position: "absolute", inset: 0 }}
    >
      <Pencahayaan variant={variant} />
      <ParallaxKamera aktif={aktif} />
      <JaringanMemori variant={variant} aktif={aktif} />
    </Canvas>
  );
}
