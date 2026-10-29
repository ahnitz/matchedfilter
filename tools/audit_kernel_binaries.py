#!/usr/bin/env python3
"""Inventory native CPU assembly and RADV shader statistics (developer tool).

Capture GPU assembly:
  MESA_SHADER_CACHE_DISABLE=1 RADV_DEBUG=shaderstats,asm \
    python tools/audit_kernel_binaries.py --capture-gpu 2>gpu.asm
Then write a machine-readable review:
  python tools/audit_kernel_binaries.py --gpu-log gpu.asm --output audit.json

Counts are static, not execution profiles. Stack operands are not a proof of
register spilling; RADV's scratch statistics are driver-specific resource data.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def cpu_inventory(library):
    text = subprocess.check_output(['objdump', '-d', '-C', '--no-show-raw-insn',
                                    str(library)], text=True)
    rows = []
    for match in re.finditer(r'^([0-9a-f]+) <([^\n]+)>:\n(.*?)(?=^[0-9a-f]+ <|\Z)',
                             text, re.M | re.S):
        name = match[2]
        if not name.startswith('ap::N_'):
            continue
        instructions = re.findall(r'^\s*[0-9a-f]+:\s+([\w.]+)\s*(.*)$', match[3], re.M)
        ops = Counter(op for op, _ in instructions)
        rows.append(dict(symbol=name, instructions=len(instructions),
                         stack_operands=sum('%rsp' in args or '%rbp' in args
                                            for _, args in instructions),
                         fma=sum(count for op, count in ops.items()
                                 if re.match(r'v(?:fm|fnm)', op)),
                         branches=sum(count for op, count in ops.items()
                                      if op.startswith('j')), opcodes=dict(ops)))
    return rows


def gpu_inventory(text, folder):
    from matchedfilter import _kernels

    def local_size(filename):
        return _kernels.record("vulkan", filename[:-len(".spv")])["local_size"]
    rows = []
    for part in text.split('AUDIT_KERNEL ')[1:]:
        filename = part.splitlines()[0]
        stats = {key: int(value) for key, value in
                 re.findall(r'^([\w -]+): (\d+)\s*$', part, re.M)}
        if not stats:
            continue
        blob = (folder / filename).read_bytes()
        ops = Counter(re.findall(r'^\t([a-z][\w.]*)\s', part, re.M))
        rows.append(dict(file=filename, sha256=hashlib.sha256(blob).hexdigest(),
                         local_size=local_size(filename),
                         stats=stats, opcodes=dict(ops)))
    captured = {row['file'] for row in rows}
    for filename, reason in re.findall(r'^AUDIT_SKIP (\S+) (.+)$', text, re.M):
        if filename in captured:
            continue
        blob = (folder / filename).read_bytes()
        rows.append(dict(file=filename, sha256=hashlib.sha256(blob).hexdigest(),
                         local_size=local_size(filename),
                         skipped=reason, stats={}, opcodes={}))
        captured.add(filename)
    return rows


def capture_gpu():
    from matchedfilter import _kernels
    from matchedfilter import _vkcompute as v
    context = v.Context(0)
    try:
        for stem, info in sorted(_kernels.manifest("vulkan")["kernels"].items()):
            if info['local_size'][0] > context.max_invocations:
                print('AUDIT_SKIP %s exceeds workgroup limit' % info['file'],
                      file=sys.stderr, flush=True)
                continue
            print('AUDIT_KERNEL ' + info['file'], file=sys.stderr, flush=True)
            # bindings and push-constant bytes as the module declares them (the manifest)
            context._build_pipeline(info['file'], info['file'],
                                    len(info['descriptors']), info['push_bytes'])
    finally:
        context.destroy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-gpu', action='store_true')
    parser.add_argument('--library', type=Path)
    parser.add_argument('--gpu-log', type=Path)
    parser.add_argument('--output', type=Path, default=Path('kernel-audit.json'))
    args = parser.parse_args()
    if args.capture_gpu:
        capture_gpu()
        return
    import matchedfilter
    from matchedfilter import _core
    library = args.library or Path(_core.__file__)
    result = dict(cpu_library=library.name,
                  cpu_sha256=hashlib.sha256(library.read_bytes()).hexdigest(),
                  cpu=cpu_inventory(library))
    if args.gpu_log:
        result['gpu'] = gpu_inventory(args.gpu_log.read_text(),
                                     Path(matchedfilter.__file__).parent / 'spirv')
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('%d CPU functions; %d GPU variants' %
          (len(result['cpu']), len(result.get('gpu', []))))


if __name__ == '__main__':
    main()
