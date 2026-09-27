"""Processor labels for the static and interactive recorded comparisons."""
import re


def cpu_label(name):
    name = name.replace('(R)', '').replace('(TM)', '')
    name = re.sub(r'^(?:AMD |Intel |13th Gen )+', '', name)
    name = re.sub(r'\s+(?:w/|with) Radeon.*$', '', name)
    name = re.sub(r'\s+\d+-Core Processor$', '', name)
    name = re.sub(r'\s+CPU @.*$', '', name)
    return name.replace('RYZEN AI MAX+', 'Ryzen AI Max+').strip()


def hardware_label(report):
    if report['device'] == 'cpu':
        suffix = 'CPU, VM' if report.get('virtualized') else 'CPU'
        return f"{cpu_label(report['cpu'])} ({suffix})"
    name = report['gpu'].replace('AMD ', '').replace('Intel(R) ', '').replace('(R)', '')
    name = re.sub(r' \((RADV|RPL-P).*$', '', name).replace('8060S Graphics', '8060S')
    if name == 'Radeon Graphics':
        name += ' — ' + cpu_label(report['cpu'])
    return name + ' (GPU)'
