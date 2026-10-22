"""What each GPU can do at most: the published or measured peaks the backends report for
matchedfilter._roofline (_x_peaks), and the sysfs reader they use. Data only."""


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


#: Measured ceilings already in the repository (source doc), for the report only.
_MEASURED = {
    "gfx1151": dict(fp16=28.2e12, fp32=22.1e12, bandwidth=198e9, source="docs/vulkan-8060s-roofline.md §1, §5"),
    "L40S": dict(fp32=72.7e12, bandwidth=623e9, source="docs/cuda-l40s-roofline.md (tools/cuda_ceilings.cu)"),
    "Apple M2 GPU": dict(fp32=3.23e12, fp16=3.33e12, bandwidth=93.4e9,
                         source="docs/metal-m2-roofline.md §0c (8 chains x 4 unrolled FMAs)"),
    "Apple M2 CPU": dict(fp32=111.5e9, fp16=223.0e9, int16=223.1e9,
                         source="docs/metal-m2-roofline.md §0c (20 FMLA/MLA chains, asm)"),
    "Zen 5": dict(fp32=324e9, source="memory note: AVX-512 FMA chains, idle core"),
}
