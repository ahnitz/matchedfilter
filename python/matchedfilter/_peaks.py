"""What each GPU can do at most: the published or measured peaks the backends report for
matchedfilter._roofline (_x_peaks), the sysfs reader they use, and the peak formulas each
backend applies to the device properties it reads (pure functions, testable without a
device)."""


def _read(path):
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return None


#: Apple GPUs: (clock GHz, cores by default, LPDDR bus bits, MT/s).
_APPLE_GPU = {"M1": (1.278, 8, 128, 4266), "M2": (1.398, 10, 128, 6400),
              "M3": (1.38, 10, 128, 6400), "M4": (1.47, 10, 128, 7500)}


#: AMD GPUs whose memory Vulkan does not describe: (bus bits, MT/s), the vendor's figure.
_AMD_MEM = {"gfx1151": (256, 8000)}


#: Measured ceilings (how each was measured), for the report only.
_MEASURED = {
    "gfx1151": dict(fp16=28.2e12, fp32=22.1e12, bandwidth=198e9, source="measured 2026-10, FMA chains and copy"),
    "L40S": dict(fp32=72.7e12, bandwidth=623e9, source="tools/cuda_ceilings.cu"),
    "Apple M2 GPU": dict(fp32=3.23e12, fp16=3.33e12, bandwidth=93.4e9,
                         source="8 chains x 4 unrolled FMAs"),
    "Apple M2 CPU": dict(fp32=111.5e9, fp16=223.0e9, int16=223.1e9,
                         source="20 FMLA/MLA chains, asm"),
    "Zen 5": dict(fp32=324e9, source="memory note: AVX-512 FMA chains, idle core"),
}


# ---- peak formulas from recorded device properties (no device needed) -----------------------
#
# Each backend's _x_peaks reads what its API (and, where the API says nothing, the kernel
# driver) reports and passes it here. A peak that cannot be derived is NaN and its reason is
# listed under out["unknown"]: no generation, chip or clock is assumed, so a driver that
# renames a device can make a peak unknown but never silently different.

NAN = float("nan")

#: fp32 FMA lanes per compute unit per clock, by AMD graphics IP major version. RDNA 1 and 2
#: (10): two SIMD32 units, 64 lanes. RDNA 3, 3.5 and 4 (11, 12): two SIMD32 units with dual
#: issue (VOPD and wave64), 128 lanes. Packed fp16 and int16 run at twice the fp32 rate on
#: all three. Older generations (GCN, CDNA) are not listed, so their peaks are unknown.
_AMD_FP32_LANES = {10: 64, 11: 128, 12: 128}


def amd_arch(major, minor, revision):
    """The LLVM target name of an AMD graphics IP version: 11.5.1 gives 'gfx1151' and
    9.0.10 gives 'gfx90a' (the revision is one hexadecimal digit)."""
    return "gfx%d%d%x" % (major, minor, revision)


def amd_ip_arch(pci_address, root="/sys/bus/pci/devices"):
    """The graphics IP of the AMD device at a PCI address ('0000:c2:00.0'), as the amdgpu
    kernel driver's IP discovery reports it (hardware block 11 is the graphics core), or None
    where that is not readable."""
    base = "%s/%s/ip_discovery/die/0/11/0/" % (root, pci_address)
    fields = [_read(base + f) for f in ("major", "minor", "revision")]
    if any(f is None for f in fields):
        return None
    try:
        return amd_arch(*(int(f.strip(), 0) for f in fields))
    except ValueError:
        return None


def max_clock_mhz(dpm_text):
    """The highest clock level in an amdgpu pp_dpm_* listing ('2: 2900Mhz'), or None."""
    import re
    levels = [int(x) for x in re.findall(r"(\d+)\s*Mhz", dpm_text or "", re.I)]
    return max(levels) if levels else None


def _all_peaks(out, fp32, fp16, int16, bandwidth, unknown):
    out.update(flops=dict(fp32=fp32, fp16=fp16, int16=int16), bandwidth=bandwidth,
               unknown=unknown)
    return out


def amd_gpu_peaks(out, cus, arch, sclk_mhz, cus_source, arch_source):
    """Theoretical peaks of an AMD GPU: CUs x fp32 lanes per CU x 2 x the highest shader
    clock, packed fp16 and int16 at twice that, and the bandwidth of its memory from the
    vendor table _AMD_MEM.

    Parameters
    ----------
    out : dict
        The record to fill (device, name and backend already set); it is returned.
    cus : int or None
        Compute units, from VK_AMD_shader_core_properties; None when not reported.
    arch : str or None
        The graphics IP as an LLVM target name ('gfx1151'); None when not known.
    sclk_mhz : int or None
        The highest shader clock level; None when not readable.
    cus_source, arch_source : str or None
        Where `cus` and `arch` came from, for the formula.

    Returns
    -------
    dict
        `out` with flops (fp32, fp16, int16), bandwidth, the formulas, and `unknown`: the
        reason for each peak that could not be derived (that peak is NaN).
    """
    import re
    unknown = []
    gen = re.match(r"gfx(\d+?)([0-9a-f]{2})$", arch or "")
    lanes = _AMD_FP32_LANES.get(int(gen.group(1))) if gen else None
    if not cus:
        unknown.append("compute-unit count (the device does not report "
                       "VK_AMD_shader_core_properties)")
    if arch is None:
        unknown.append("graphics architecture (neither amdgpu IP discovery nor the device name "
                       "gives it)")
    elif lanes is None:
        unknown.append("fp32 lanes per compute unit of %s (no entry in _AMD_FP32_LANES)" % arch)
    if not sclk_mhz:
        unknown.append("shader clock (pp_dpm_sclk not readable)")
    ghz = sclk_mhz / 1e3 if sclk_mhz else NAN
    fp32 = cus * lanes * 2 * ghz * 1e9 if (cus and lanes and sclk_mhz) else NAN
    bus, mts = _AMD_MEM.get(arch, (None, None))
    if bus is None:
        unknown.append("memory bandwidth of %s (no entry in _AMD_MEM; Vulkan does not "
                       "describe memory)" % (arch or "this device"))
    out.update(arch=arch, cus=cus, clock_ghz=ghz,
               formula="%s CUs (%s) x %s fp32 lanes (%s) x 2 x %s GHz max sclk; fp16/int16 "
                       "packed: 2x" % (cus, cus_source or "unknown", lanes, arch or "unknown arch",
                                       "%.2f" % ghz if sclk_mhz else "unknown"),
               arch_source=arch_source,
               bandwidth_formula=("%d-bit x %d MT/s / 8 (vendor figure; Vulkan does not describe "
                                  "memory)" % (bus, mts)) if bus else "unknown",
               measured=_MEASURED.get(arch))
    return _all_peaks(out, fp32, 2 * fp32, 2 * fp32,
                      bus * mts * 1e6 / 8 if bus else NAN, unknown)


#: CUDA fp32 lanes per SM and vector fp16 lanes per SM by compute capability (CUDA C
#: Programming Guide, arithmetic instruction throughput); vector fp16 runs at the fp32 rate
#: from 8.6 on. A compute capability not listed has unknown peaks.
_CUDA_LANES = {(7, 0): (64, 128), (7, 5): (64, 128), (8, 0): (64, 256), (8, 6): (128, 128),
               (8, 7): (128, 128), (8, 9): (128, 128), (9, 0): (128, 128)}


def cuda_gpu_peaks(out, sms, clock_khz, memory_khz, bus_bits, cc):
    """Theoretical peaks of a CUDA device from its driver attributes: SMs x lanes x 2 x the
    boost clock (int16 at the fp32 rate, tensor cores not counted), and 2 x memory clock x bus
    width / 8. A compute capability without a _CUDA_LANES entry, or an attribute the driver
    reports as zero, makes the peaks that need it NaN and lists the reason under `unknown`;
    `out` is filled and returned."""
    unknown = []
    lanes = _CUDA_LANES.get(tuple(cc))
    if lanes is None:
        unknown.append("lanes per SM of compute capability %d.%d (no entry in _CUDA_LANES)"
                       % tuple(cc))
    if not (sms and clock_khz):
        unknown.append("SM count or clock (driver attribute zero)")
    ghz = clock_khz / 1e6 if clock_khz else NAN
    fp32, fp16 = lanes or (None, None)
    ok = bool(lanes and sms and clock_khz)
    if not (memory_khz and bus_bits):
        unknown.append("memory clock or bus width (driver attribute zero)")
    out.update(sms=sms, cc=tuple(cc), clock_ghz=ghz,
               formula="%s SMs x %s fp32 lanes (fp16 %s) x 2 x %s GHz boost; int16 at the fp32 "
                       "rate; tensor cores not counted" % (
                           sms, fp32, fp16, "%.3f" % ghz if clock_khz else "unknown"),
               bandwidth_formula="2 x %.0f MHz memory clock x %d-bit bus / 8" % (
                   (memory_khz or 0) / 1e3, bus_bits or 0),
               measured=_MEASURED.get("L40S") if "L40S" in (out.get("name") or "") else None)
    f32 = sms * fp32 * 2 * ghz * 1e9 if ok else NAN
    return _all_peaks(out, f32, sms * fp16 * 2 * ghz * 1e9 if ok else NAN, f32,
                      2 * memory_khz * 1e3 * bus_bits / 8 if (memory_khz and bus_bits) else NAN,
                      unknown)


def apple_gpu_peaks(out, cores):
    """Theoretical peaks of an Apple GPU named in out['name'] ('Apple M2', 'Apple M2 Pro'):
    cores x 128 ALUs x 2 x the generation's GPU clock (fp16 at the fp32 rate), and the base
    chip's LPDDR bus x MT/s / 8. The bus of a Pro, Max or Ultra part differs from the base
    chip's, so its bandwidth is unknown; an unlisted generation has unknown peaks. cores: the
    ioreg gpu-core-count, or None for the base chip's default. `out` is filled and returned."""
    import re
    unknown = []
    m = re.search(r"\b(M\d+)\b(?:\s+(Pro|Max|Ultra))?", out.get("name") or "")
    chip = m.group(1) if m and m.group(1) in _APPLE_GPU else None
    variant = m.group(2) if m else None
    if chip is None:
        unknown.append("Apple GPU generation of %r (no entry in _APPLE_GPU)" % out.get("name"))
        ghz = NAN
        bw = NAN
    else:
        ghz, default_cores, bus, mts = _APPLE_GPU[chip]
        cores = cores or (None if variant else default_cores)
        bw = NAN if variant else bus * mts * 1e6 / 8
        if variant:
            unknown.append("memory bus of the M %s variant (only base chips are in _APPLE_GPU)"
                           % variant)
    if not cores:
        unknown.append("GPU core count (ioreg gpu-core-count not readable)")
    f = cores * 128 * 2 * ghz * 1e9 if (cores and chip) else NAN
    out.update(cores=cores, clock_ghz=ghz,
               formula="%s cores (ioreg gpu-core-count) x 128 ALUs x 2 x %s GHz (vendor clock); "
                       "fp16 at the fp32 rate" % (cores, "%.3f" % ghz if chip else "unknown"),
               bandwidth_formula=("%d-bit LPDDR x %d MT/s / 8 (vendor figure)" % (bus, mts))
               if (chip and not variant) else "unknown",
               measured=_MEASURED.get("Apple %s GPU" % chip) if chip and not variant else None)
    return _all_peaks(out, f, f, f, bw, unknown)
