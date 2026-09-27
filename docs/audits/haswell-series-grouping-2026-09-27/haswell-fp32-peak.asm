
/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/kernel-study/peak_fp32:     file format elf64-x86-64


Disassembly of section .init:

0000000000001000 <_init>:
    1000:	f3 0f 1e fa          	endbr64 
    1004:	48 83 ec 08          	sub    $0x8,%rsp
    1008:	48 8b 05 d9 2f 00 00 	mov    0x2fd9(%rip),%rax        # 3fe8 <__gmon_start__>
    100f:	48 85 c0             	test   %rax,%rax
    1012:	74 02                	je     1016 <_init+0x16>
    1014:	ff d0                	callq  *%rax
    1016:	48 83 c4 08          	add    $0x8,%rsp
    101a:	c3                   	retq   

Disassembly of section .plt:

0000000000001020 <.plt>:
    1020:	ff 35 5a 2f 00 00    	pushq  0x2f5a(%rip)        # 3f80 <_GLOBAL_OFFSET_TABLE_+0x8>
    1026:	f2 ff 25 5b 2f 00 00 	bnd jmpq *0x2f5b(%rip)        # 3f88 <_GLOBAL_OFFSET_TABLE_+0x10>
    102d:	0f 1f 00             	nopl   (%rax)
    1030:	f3 0f 1e fa          	endbr64 
    1034:	68 00 00 00 00       	pushq  $0x0
    1039:	f2 e9 e1 ff ff ff    	bnd jmpq 1020 <.plt>
    103f:	90                   	nop
    1040:	f3 0f 1e fa          	endbr64 
    1044:	68 01 00 00 00       	pushq  $0x1
    1049:	f2 e9 d1 ff ff ff    	bnd jmpq 1020 <.plt>
    104f:	90                   	nop
    1050:	f3 0f 1e fa          	endbr64 
    1054:	68 02 00 00 00       	pushq  $0x2
    1059:	f2 e9 c1 ff ff ff    	bnd jmpq 1020 <.plt>
    105f:	90                   	nop
    1060:	f3 0f 1e fa          	endbr64 
    1064:	68 03 00 00 00       	pushq  $0x3
    1069:	f2 e9 b1 ff ff ff    	bnd jmpq 1020 <.plt>
    106f:	90                   	nop
    1070:	f3 0f 1e fa          	endbr64 
    1074:	68 04 00 00 00       	pushq  $0x4
    1079:	f2 e9 a1 ff ff ff    	bnd jmpq 1020 <.plt>
    107f:	90                   	nop
    1080:	f3 0f 1e fa          	endbr64 
    1084:	68 05 00 00 00       	pushq  $0x5
    1089:	f2 e9 91 ff ff ff    	bnd jmpq 1020 <.plt>
    108f:	90                   	nop
    1090:	f3 0f 1e fa          	endbr64 
    1094:	68 06 00 00 00       	pushq  $0x6
    1099:	f2 e9 81 ff ff ff    	bnd jmpq 1020 <.plt>
    109f:	90                   	nop
    10a0:	f3 0f 1e fa          	endbr64 
    10a4:	68 07 00 00 00       	pushq  $0x7
    10a9:	f2 e9 71 ff ff ff    	bnd jmpq 1020 <.plt>
    10af:	90                   	nop
    10b0:	f3 0f 1e fa          	endbr64 
    10b4:	68 08 00 00 00       	pushq  $0x8
    10b9:	f2 e9 61 ff ff ff    	bnd jmpq 1020 <.plt>
    10bf:	90                   	nop

Disassembly of section .plt.got:

00000000000010c0 <__cxa_finalize@plt>:
    10c0:	f3 0f 1e fa          	endbr64 
    10c4:	f2 ff 25 2d 2f 00 00 	bnd jmpq *0x2f2d(%rip)        # 3ff8 <__cxa_finalize@GLIBC_2.2.5>
    10cb:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)

Disassembly of section .plt.sec:

00000000000010d0 <__errno_location@plt>:
    10d0:	f3 0f 1e fa          	endbr64 
    10d4:	f2 ff 25 b5 2e 00 00 	bnd jmpq *0x2eb5(%rip)        # 3f90 <__errno_location@GLIBC_2.2.5>
    10db:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)

00000000000010e0 <puts@plt>:
    10e0:	f3 0f 1e fa          	endbr64 
    10e4:	f2 ff 25 ad 2e 00 00 	bnd jmpq *0x2ead(%rip)        # 3f98 <puts@GLIBC_2.2.5>
    10eb:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)

00000000000010f0 <clock_gettime@plt>:
    10f0:	f3 0f 1e fa          	endbr64 
    10f4:	f2 ff 25 a5 2e 00 00 	bnd jmpq *0x2ea5(%rip)        # 3fa0 <clock_gettime@GLIBC_2.17>
    10fb:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)

0000000000001100 <__stack_chk_fail@plt>:
    1100:	f3 0f 1e fa          	endbr64 
    1104:	f2 ff 25 9d 2e 00 00 	bnd jmpq *0x2e9d(%rip)        # 3fa8 <__stack_chk_fail@GLIBC_2.4>
    110b:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)

0000000000001110 <close@plt>:
    1110:	f3 0f 1e fa          	endbr64 
    1114:	f2 ff 25 95 2e 00 00 	bnd jmpq *0x2e95(%rip)        # 3fb0 <close@GLIBC_2.2.5>
    111b:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)

0000000000001120 <read@plt>:
    1120:	f3 0f 1e fa          	endbr64 
    1124:	f2 ff 25 8d 2e 00 00 	bnd jmpq *0x2e8d(%rip)        # 3fb8 <read@GLIBC_2.2.5>
    112b:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)

0000000000001130 <syscall@plt>:
    1130:	f3 0f 1e fa          	endbr64 
    1134:	f2 ff 25 85 2e 00 00 	bnd jmpq *0x2e85(%rip)        # 3fc0 <syscall@GLIBC_2.2.5>
    113b:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)

0000000000001140 <__printf_chk@plt>:
    1140:	f3 0f 1e fa          	endbr64 
    1144:	f2 ff 25 7d 2e 00 00 	bnd jmpq *0x2e7d(%rip)        # 3fc8 <__printf_chk@GLIBC_2.3.4>
    114b:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)

0000000000001150 <strerror@plt>:
    1150:	f3 0f 1e fa          	endbr64 
    1154:	f2 ff 25 75 2e 00 00 	bnd jmpq *0x2e75(%rip)        # 3fd0 <strerror@GLIBC_2.2.5>
    115b:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)

Disassembly of section .text:

0000000000001160 <main>:
    1160:	f3 0f 1e fa          	endbr64 
    1164:	41 57                	push   %r15
    1166:	b9 0c 00 00 00       	mov    $0xc,%ecx
    116b:	31 d2                	xor    %edx,%edx
    116d:	45 31 c9             	xor    %r9d,%r9d
    1170:	41 56                	push   %r14
    1172:	41 b8 ff ff ff ff    	mov    $0xffffffff,%r8d
    1178:	41 55                	push   %r13
    117a:	41 54                	push   %r12
    117c:	55                   	push   %rbp
    117d:	53                   	push   %rbx
    117e:	48 81 ec d8 00 00 00 	sub    $0xd8,%rsp
    1185:	64 48 8b 04 25 28 00 	mov    %fs:0x28,%rax
    118c:	00 00 
    118e:	48 89 84 24 c8 00 00 	mov    %rax,0xc8(%rsp)
    1195:	00 
    1196:	31 c0                	xor    %eax,%eax
    1198:	48 8d 7c 24 60       	lea    0x60(%rsp),%rdi
    119d:	48 8d 74 24 50       	lea    0x50(%rsp),%rsi
    11a2:	48 c7 44 24 58 00 00 	movq   $0x0,0x58(%rsp)
    11a9:	00 00 
    11ab:	f3 48 ab             	rep stos %rax,%es:(%rdi)
    11ae:	b9 ff ff ff ff       	mov    $0xffffffff,%ecx
    11b3:	bf 2a 01 00 00       	mov    $0x12a,%edi
    11b8:	48 b8 00 00 00 00 70 	movabs $0x7000000000,%rax
    11bf:	00 00 00 
    11c2:	48 89 44 24 50       	mov    %rax,0x50(%rsp)
    11c7:	31 c0                	xor    %eax,%eax
    11c9:	c6 44 24 78 60       	movb   $0x60,0x78(%rsp)
    11ce:	e8 5d ff ff ff       	callq  1130 <syscall@plt>
    11d3:	48 8d 0d 37 0e 00 00 	lea    0xe37(%rip),%rcx        # 2011 <_IO_stdin_used+0x11>
    11da:	48 8d 15 29 0e 00 00 	lea    0xe29(%rip),%rdx        # 200a <_IO_stdin_used+0xa>
    11e1:	48 89 44 24 18       	mov    %rax,0x18(%rsp)
    11e6:	41 89 c4             	mov    %eax,%r12d
    11e9:	85 c0                	test   %eax,%eax
    11eb:	0f 88 4a 02 00 00    	js     143b <main+0x2db>
    11f1:	48 8d 35 20 0e 00 00 	lea    0xe20(%rip),%rsi        # 2018 <_IO_stdin_used+0x18>
    11f8:	bf 01 00 00 00       	mov    $0x1,%edi
    11fd:	31 c0                	xor    %eax,%eax
    11ff:	31 ed                	xor    %ebp,%ebp
    1201:	e8 3a ff ff ff       	callq  1140 <__printf_chk@plt>
    1206:	bf 80 96 98 00       	mov    $0x989680,%edi
    120b:	48 8d 5c 24 40       	lea    0x40(%rsp),%rbx
    1210:	4c 8d 6c 24 2c       	lea    0x2c(%rsp),%r13
    1215:	e8 36 03 00 00       	callq  1550 <peak>
    121a:	48 8d 44 24 30       	lea    0x30(%rsp),%rax
    121f:	48 89 44 24 10       	mov    %rax,0x10(%rsp)
    1224:	c5 fa 11 44 24 28    	vmovss %xmm0,0x28(%rsp)
    122a:	eb 2d                	jmp    1259 <main+0xf9>
    122c:	0f 1f 40 00          	nopl   0x0(%rax)
    1230:	48 8d 15 d8 0d 00 00 	lea    0xdd8(%rip),%rdx        # 200f <_IO_stdin_used+0xf>
    1237:	bf 01 00 00 00       	mov    $0x1,%edi
    123c:	b8 04 00 00 00       	mov    $0x4,%eax
    1241:	48 8d 35 50 0e 00 00 	lea    0xe50(%rip),%rsi        # 2098 <_IO_stdin_used+0x98>
    1248:	e8 f3 fe ff ff       	callq  1140 <__printf_chk@plt>
    124d:	83 fd 08             	cmp    $0x8,%ebp
    1250:	0f 84 a2 01 00 00    	je     13f8 <main+0x298>
    1256:	83 c5 01             	add    $0x1,%ebp
    1259:	48 c7 44 24 30 00 00 	movq   $0x0,0x30(%rsp)
    1260:	00 00 
    1262:	48 c7 44 24 38 00 00 	movq   $0x0,0x38(%rsp)
    1269:	00 00 
    126b:	45 85 e4             	test   %r12d,%r12d
    126e:	78 12                	js     1282 <main+0x122>
    1270:	48 8b 74 24 10       	mov    0x10(%rsp),%rsi
    1275:	ba 08 00 00 00       	mov    $0x8,%edx
    127a:	44 89 e7             	mov    %r12d,%edi
    127d:	e8 9e fe ff ff       	callq  1120 <read@plt>
    1282:	48 89 de             	mov    %rbx,%rsi
    1285:	bf 03 00 00 00       	mov    $0x3,%edi
    128a:	e8 61 fe ff ff       	callq  10f0 <clock_gettime@plt>
    128f:	c5 d9 57 e4          	vxorpd %xmm4,%xmm4,%xmm4
    1293:	48 89 de             	mov    %rbx,%rsi
    1296:	bf 04 00 00 00       	mov    $0x4,%edi
    129b:	c4 e1 db 2a 4c 24 40 	vcvtsi2sdq 0x40(%rsp),%xmm4,%xmm1
    12a2:	c4 e1 db 2a 44 24 48 	vcvtsi2sdq 0x48(%rsp),%xmm4,%xmm0
    12a9:	c4 e2 f1 99 05 2e 10 	vfmadd132sd 0x102e(%rip),%xmm1,%xmm0        # 22e0 <_IO_stdin_used+0x2e0>
    12b0:	00 00 
    12b2:	c5 fb 11 44 24 08    	vmovsd %xmm0,0x8(%rsp)
    12b8:	e8 33 fe ff ff       	callq  10f0 <clock_gettime@plt>
    12bd:	c5 d9 57 e4          	vxorpd %xmm4,%xmm4,%xmm4
    12c1:	c4 e1 db 2a 4c 24 48 	vcvtsi2sdq 0x48(%rsp),%xmm4,%xmm1
    12c8:	c4 e1 db 2a 44 24 40 	vcvtsi2sdq 0x40(%rsp),%xmm4,%xmm0
    12cf:	c4 e2 f9 99 0d 08 10 	vfmadd132sd 0x1008(%rip),%xmm0,%xmm1        # 22e0 <_IO_stdin_used+0x2e0>
    12d6:	00 00 
    12d8:	c5 fb 11 0c 24       	vmovsd %xmm1,(%rsp)
    12dd:	0f 01 f9             	rdtscp 
    12e0:	bf 00 e1 f5 05       	mov    $0x5f5e100,%edi
    12e5:	49 89 c6             	mov    %rax,%r14
    12e8:	48 c1 e2 20          	shl    $0x20,%rdx
    12ec:	41 89 4d 00          	mov    %ecx,0x0(%r13)
    12f0:	49 09 d6             	or     %rdx,%r14
    12f3:	e8 58 02 00 00       	callq  1550 <peak>
    12f8:	c5 fa 11 44 24 28    	vmovss %xmm0,0x28(%rsp)
    12fe:	0f 01 f9             	rdtscp 
    1301:	bf 04 00 00 00       	mov    $0x4,%edi
    1306:	48 c1 e2 20          	shl    $0x20,%rdx
    130a:	49 89 c7             	mov    %rax,%r15
    130d:	48 89 de             	mov    %rbx,%rsi
    1310:	41 89 4d 00          	mov    %ecx,0x0(%r13)
    1314:	49 09 d7             	or     %rdx,%r15
    1317:	e8 d4 fd ff ff       	callq  10f0 <clock_gettime@plt>
    131c:	c5 d9 57 e4          	vxorpd %xmm4,%xmm4,%xmm4
    1320:	48 89 de             	mov    %rbx,%rsi
    1323:	bf 03 00 00 00       	mov    $0x3,%edi
    1328:	c4 e1 db 2a 44 24 48 	vcvtsi2sdq 0x48(%rsp),%xmm4,%xmm0
    132f:	c5 f9 28 c8          	vmovapd %xmm0,%xmm1
    1333:	c4 e1 db 2a 44 24 40 	vcvtsi2sdq 0x40(%rsp),%xmm4,%xmm0
    133a:	c4 e2 f1 b9 05 9d 0f 	vfmadd231sd 0xf9d(%rip),%xmm1,%xmm0        # 22e0 <_IO_stdin_used+0x2e0>
    1341:	00 00 
    1343:	c5 fb 5c 04 24       	vsubsd (%rsp),%xmm0,%xmm0
    1348:	c5 fb 11 04 24       	vmovsd %xmm0,(%rsp)
    134d:	e8 9e fd ff ff       	callq  10f0 <clock_gettime@plt>
    1352:	c5 d9 57 e4          	vxorpd %xmm4,%xmm4,%xmm4
    1356:	45 85 e4             	test   %r12d,%r12d
    1359:	c5 fb 10 04 24       	vmovsd (%rsp),%xmm0
    135e:	c4 e1 db 2a 4c 24 48 	vcvtsi2sdq 0x48(%rsp),%xmm4,%xmm1
    1365:	c5 f9 28 d1          	vmovapd %xmm1,%xmm2
    1369:	c4 e1 db 2a 4c 24 40 	vcvtsi2sdq 0x40(%rsp),%xmm4,%xmm1
    1370:	c4 e2 e9 b9 0d 67 0f 	vfmadd231sd 0xf67(%rip),%xmm2,%xmm1        # 22e0 <_IO_stdin_used+0x2e0>
    1377:	00 00 
    1379:	c5 f3 5c 4c 24 08    	vsubsd 0x8(%rsp),%xmm1,%xmm1
    137f:	78 23                	js     13a4 <main+0x244>
    1381:	48 8d 74 24 38       	lea    0x38(%rsp),%rsi
    1386:	ba 08 00 00 00       	mov    $0x8,%edx
    138b:	44 89 e7             	mov    %r12d,%edi
    138e:	c5 fb 11 4c 24 08    	vmovsd %xmm1,0x8(%rsp)
    1394:	e8 87 fd ff ff       	callq  1120 <read@plt>
    1399:	c5 fb 10 4c 24 08    	vmovsd 0x8(%rsp),%xmm1
    139f:	c5 fb 10 04 24       	vmovsd (%rsp),%xmm0
    13a4:	c5 fa 10 5c 24 28    	vmovss 0x28(%rsp),%xmm3
    13aa:	c5 fb 10 2d 36 0f 00 	vmovsd 0xf36(%rip),%xmm5        # 22e8 <_IO_stdin_used+0x2e8>
    13b1:	00 
    13b2:	4c 89 f9             	mov    %r15,%rcx
    13b5:	4c 8b 44 24 38       	mov    0x38(%rsp),%r8
    13ba:	4c 29 f1             	sub    %r14,%rcx
    13bd:	4c 2b 44 24 30       	sub    0x30(%rsp),%r8
    13c2:	c5 d3 5e d0          	vdivsd %xmm0,%xmm5,%xmm2
    13c6:	c5 e2 5a db          	vcvtss2sd %xmm3,%xmm3,%xmm3
    13ca:	85 ed                	test   %ebp,%ebp
    13cc:	0f 85 5e fe ff ff    	jne    1230 <main+0xd0>
    13d2:	48 8d 15 38 0c 00 00 	lea    0xc38(%rip),%rdx        # 2011 <_IO_stdin_used+0x11>
    13d9:	bf 01 00 00 00       	mov    $0x1,%edi
    13de:	b8 04 00 00 00       	mov    $0x4,%eax
    13e3:	48 8d 35 ae 0c 00 00 	lea    0xcae(%rip),%rsi        # 2098 <_IO_stdin_used+0x98>
    13ea:	e8 51 fd ff ff       	callq  1140 <__printf_chk@plt>
    13ef:	e9 62 fe ff ff       	jmpq   1256 <main+0xf6>
    13f4:	0f 1f 40 00          	nopl   0x0(%rax)
    13f8:	48 8d 3d 13 0c 00 00 	lea    0xc13(%rip),%rdi        # 2012 <_IO_stdin_used+0x12>
    13ff:	e8 dc fc ff ff       	callq  10e0 <puts@plt>
    1404:	48 8b 44 24 18       	mov    0x18(%rsp),%rax
    1409:	85 c0                	test   %eax,%eax
    140b:	78 07                	js     1414 <main+0x2b4>
    140d:	89 c7                	mov    %eax,%edi
    140f:	e8 fc fc ff ff       	callq  1110 <close@plt>
    1414:	48 8b 84 24 c8 00 00 	mov    0xc8(%rsp),%rax
    141b:	00 
    141c:	64 48 33 04 25 28 00 	xor    %fs:0x28,%rax
    1423:	00 00 
    1425:	75 2f                	jne    1456 <main+0x2f6>
    1427:	48 81 c4 d8 00 00 00 	add    $0xd8,%rsp
    142e:	31 c0                	xor    %eax,%eax
    1430:	5b                   	pop    %rbx
    1431:	5d                   	pop    %rbp
    1432:	41 5c                	pop    %r12
    1434:	41 5d                	pop    %r13
    1436:	41 5e                	pop    %r14
    1438:	41 5f                	pop    %r15
    143a:	c3                   	retq   
    143b:	e8 90 fc ff ff       	callq  10d0 <__errno_location@plt>
    1440:	8b 38                	mov    (%rax),%edi
    1442:	e8 09 fd ff ff       	callq  1150 <strerror@plt>
    1447:	48 8d 15 b6 0b 00 00 	lea    0xbb6(%rip),%rdx        # 2004 <_IO_stdin_used+0x4>
    144e:	48 89 c1             	mov    %rax,%rcx
    1451:	e9 9b fd ff ff       	jmpq   11f1 <main+0x91>
    1456:	e8 a5 fc ff ff       	callq  1100 <__stack_chk_fail@plt>
    145b:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)

0000000000001460 <_start>:
    1460:	f3 0f 1e fa          	endbr64 
    1464:	31 ed                	xor    %ebp,%ebp
    1466:	49 89 d1             	mov    %rdx,%r9
    1469:	5e                   	pop    %rsi
    146a:	48 89 e2             	mov    %rsp,%rdx
    146d:	48 83 e4 f0          	and    $0xfffffffffffffff0,%rsp
    1471:	50                   	push   %rax
    1472:	54                   	push   %rsp
    1473:	4c 8d 05 56 02 00 00 	lea    0x256(%rip),%r8        # 16d0 <__libc_csu_fini>
    147a:	48 8d 0d df 01 00 00 	lea    0x1df(%rip),%rcx        # 1660 <__libc_csu_init>
    1481:	48 8d 3d d8 fc ff ff 	lea    -0x328(%rip),%rdi        # 1160 <main>
    1488:	ff 15 52 2b 00 00    	callq  *0x2b52(%rip)        # 3fe0 <__libc_start_main@GLIBC_2.2.5>
    148e:	f4                   	hlt    
    148f:	90                   	nop

0000000000001490 <deregister_tm_clones>:
    1490:	48 8d 3d 79 2b 00 00 	lea    0x2b79(%rip),%rdi        # 4010 <__TMC_END__>
    1497:	48 8d 05 72 2b 00 00 	lea    0x2b72(%rip),%rax        # 4010 <__TMC_END__>
    149e:	48 39 f8             	cmp    %rdi,%rax
    14a1:	74 15                	je     14b8 <deregister_tm_clones+0x28>
    14a3:	48 8b 05 2e 2b 00 00 	mov    0x2b2e(%rip),%rax        # 3fd8 <_ITM_deregisterTMCloneTable>
    14aa:	48 85 c0             	test   %rax,%rax
    14ad:	74 09                	je     14b8 <deregister_tm_clones+0x28>
    14af:	ff e0                	jmpq   *%rax
    14b1:	0f 1f 80 00 00 00 00 	nopl   0x0(%rax)
    14b8:	c3                   	retq   
    14b9:	0f 1f 80 00 00 00 00 	nopl   0x0(%rax)

00000000000014c0 <register_tm_clones>:
    14c0:	48 8d 3d 49 2b 00 00 	lea    0x2b49(%rip),%rdi        # 4010 <__TMC_END__>
    14c7:	48 8d 35 42 2b 00 00 	lea    0x2b42(%rip),%rsi        # 4010 <__TMC_END__>
    14ce:	48 29 fe             	sub    %rdi,%rsi
    14d1:	48 89 f0             	mov    %rsi,%rax
    14d4:	48 c1 ee 3f          	shr    $0x3f,%rsi
    14d8:	48 c1 f8 03          	sar    $0x3,%rax
    14dc:	48 01 c6             	add    %rax,%rsi
    14df:	48 d1 fe             	sar    %rsi
    14e2:	74 14                	je     14f8 <register_tm_clones+0x38>
    14e4:	48 8b 05 05 2b 00 00 	mov    0x2b05(%rip),%rax        # 3ff0 <_ITM_registerTMCloneTable>
    14eb:	48 85 c0             	test   %rax,%rax
    14ee:	74 08                	je     14f8 <register_tm_clones+0x38>
    14f0:	ff e0                	jmpq   *%rax
    14f2:	66 0f 1f 44 00 00    	nopw   0x0(%rax,%rax,1)
    14f8:	c3                   	retq   
    14f9:	0f 1f 80 00 00 00 00 	nopl   0x0(%rax)

0000000000001500 <__do_global_dtors_aux>:
    1500:	f3 0f 1e fa          	endbr64 
    1504:	80 3d 05 2b 00 00 00 	cmpb   $0x0,0x2b05(%rip)        # 4010 <__TMC_END__>
    150b:	75 2b                	jne    1538 <__do_global_dtors_aux+0x38>
    150d:	55                   	push   %rbp
    150e:	48 83 3d e2 2a 00 00 	cmpq   $0x0,0x2ae2(%rip)        # 3ff8 <__cxa_finalize@GLIBC_2.2.5>
    1515:	00 
    1516:	48 89 e5             	mov    %rsp,%rbp
    1519:	74 0c                	je     1527 <__do_global_dtors_aux+0x27>
    151b:	48 8b 3d e6 2a 00 00 	mov    0x2ae6(%rip),%rdi        # 4008 <__dso_handle>
    1522:	e8 99 fb ff ff       	callq  10c0 <__cxa_finalize@plt>
    1527:	e8 64 ff ff ff       	callq  1490 <deregister_tm_clones>
    152c:	c6 05 dd 2a 00 00 01 	movb   $0x1,0x2add(%rip)        # 4010 <__TMC_END__>
    1533:	5d                   	pop    %rbp
    1534:	c3                   	retq   
    1535:	0f 1f 00             	nopl   (%rax)
    1538:	c3                   	retq   
    1539:	0f 1f 80 00 00 00 00 	nopl   0x0(%rax)

0000000000001540 <frame_dummy>:
    1540:	f3 0f 1e fa          	endbr64 
    1544:	e9 77 ff ff ff       	jmpq   14c0 <register_tm_clones>
    1549:	0f 1f 80 00 00 00 00 	nopl   0x0(%rax)

0000000000001550 <peak>:
    1550:	48 85 ff             	test   %rdi,%rdi
    1553:	0f 8e f7 00 00 00    	jle    1650 <peak+0x100>
    1559:	c5 7c 28 05 9f 0b 00 	vmovaps 0xb9f(%rip),%ymm8        # 2100 <_IO_stdin_used+0x100>
    1560:	00 
    1561:	c5 fc 28 2d b7 0b 00 	vmovaps 0xbb7(%rip),%ymm5        # 2120 <_IO_stdin_used+0x120>
    1568:	00 
    1569:	31 c0                	xor    %eax,%eax
    156b:	c5 7c 28 0d cd 0b 00 	vmovaps 0xbcd(%rip),%ymm9        # 2140 <_IO_stdin_used+0x140>
    1572:	00 
    1573:	c5 fc 28 1d e5 0b 00 	vmovaps 0xbe5(%rip),%ymm3        # 2160 <_IO_stdin_used+0x160>
    157a:	00 
    157b:	c5 7c 28 15 fd 0b 00 	vmovaps 0xbfd(%rip),%ymm10        # 2180 <_IO_stdin_used+0x180>
    1582:	00 
    1583:	c5 fc 28 35 15 0c 00 	vmovaps 0xc15(%rip),%ymm6        # 21a0 <_IO_stdin_used+0x1a0>
    158a:	00 
    158b:	c5 7c 28 1d 2d 0c 00 	vmovaps 0xc2d(%rip),%ymm11        # 21c0 <_IO_stdin_used+0x1c0>
    1592:	00 
    1593:	c5 fc 28 25 45 0c 00 	vmovaps 0xc45(%rip),%ymm4        # 21e0 <_IO_stdin_used+0x1e0>
    159a:	00 
    159b:	c5 7c 28 25 5d 0c 00 	vmovaps 0xc5d(%rip),%ymm12        # 2200 <_IO_stdin_used+0x200>
    15a2:	00 
    15a3:	c5 fc 28 3d 75 0c 00 	vmovaps 0xc75(%rip),%ymm7        # 2220 <_IO_stdin_used+0x220>
    15aa:	00 
    15ab:	c5 7c 28 2d 8d 0c 00 	vmovaps 0xc8d(%rip),%ymm13        # 2240 <_IO_stdin_used+0x240>
    15b2:	00 
    15b3:	c5 fc 28 15 a5 0c 00 	vmovaps 0xca5(%rip),%ymm2        # 2260 <_IO_stdin_used+0x260>
    15ba:	00 
    15bb:	c5 fc 28 0d dd 0c 00 	vmovaps 0xcdd(%rip),%ymm1        # 22a0 <_IO_stdin_used+0x2a0>
    15c2:	00 
    15c3:	c5 fc 28 05 f5 0c 00 	vmovaps 0xcf5(%rip),%ymm0        # 22c0 <_IO_stdin_used+0x2c0>
    15ca:	00 
    15cb:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)
    15d0:	c4 e2 7d 98 d1       	vfmadd132ps %ymm1,%ymm0,%ymm2
    15d5:	c4 62 7d 98 e9       	vfmadd132ps %ymm1,%ymm0,%ymm13
    15da:	48 83 c0 01          	add    $0x1,%rax
    15de:	c4 e2 7d 98 f9       	vfmadd132ps %ymm1,%ymm0,%ymm7
    15e3:	c4 62 7d 98 e1       	vfmadd132ps %ymm1,%ymm0,%ymm12
    15e8:	c4 e2 7d 98 e1       	vfmadd132ps %ymm1,%ymm0,%ymm4
    15ed:	c4 62 7d 98 d9       	vfmadd132ps %ymm1,%ymm0,%ymm11
    15f2:	c4 e2 7d 98 f1       	vfmadd132ps %ymm1,%ymm0,%ymm6
    15f7:	c4 62 7d 98 d1       	vfmadd132ps %ymm1,%ymm0,%ymm10
    15fc:	c4 e2 7d 98 d9       	vfmadd132ps %ymm1,%ymm0,%ymm3
    1601:	c4 62 7d 98 c9       	vfmadd132ps %ymm1,%ymm0,%ymm9
    1606:	c4 e2 7d 98 e9       	vfmadd132ps %ymm1,%ymm0,%ymm5
    160b:	c4 62 7d 98 c1       	vfmadd132ps %ymm1,%ymm0,%ymm8
    1610:	48 39 c7             	cmp    %rax,%rdi
    1613:	75 bb                	jne    15d0 <peak+0x80>
    1615:	c4 c1 6c 58 d5       	vaddps %ymm13,%ymm2,%ymm2
    161a:	c4 c1 44 58 c4       	vaddps %ymm12,%ymm7,%ymm0
    161f:	c4 c1 5c 58 e3       	vaddps %ymm11,%ymm4,%ymm4
    1624:	c4 c1 4c 58 f2       	vaddps %ymm10,%ymm6,%ymm6
    1629:	c4 c1 64 58 d9       	vaddps %ymm9,%ymm3,%ymm3
    162e:	c4 c1 54 58 e8       	vaddps %ymm8,%ymm5,%ymm5
    1633:	c5 ec 58 c0          	vaddps %ymm0,%ymm2,%ymm0
    1637:	c5 dc 58 e6          	vaddps %ymm6,%ymm4,%ymm4
    163b:	c5 e4 58 dd          	vaddps %ymm5,%ymm3,%ymm3
    163f:	c5 fc 58 c4          	vaddps %ymm4,%ymm0,%ymm0
    1643:	c5 fc 58 c3          	vaddps %ymm3,%ymm0,%ymm0
    1647:	c5 f8 77             	vzeroupper 
    164a:	c3                   	retq   
    164b:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)
    1650:	c5 fc 28 05 28 0c 00 	vmovaps 0xc28(%rip),%ymm0        # 2280 <_IO_stdin_used+0x280>
    1657:	00 
    1658:	c5 f8 77             	vzeroupper 
    165b:	c3                   	retq   
    165c:	0f 1f 40 00          	nopl   0x0(%rax)

0000000000001660 <__libc_csu_init>:
    1660:	f3 0f 1e fa          	endbr64 
    1664:	41 57                	push   %r15
    1666:	4c 8d 3d 0b 27 00 00 	lea    0x270b(%rip),%r15        # 3d78 <__frame_dummy_init_array_entry>
    166d:	41 56                	push   %r14
    166f:	49 89 d6             	mov    %rdx,%r14
    1672:	41 55                	push   %r13
    1674:	49 89 f5             	mov    %rsi,%r13
    1677:	41 54                	push   %r12
    1679:	41 89 fc             	mov    %edi,%r12d
    167c:	55                   	push   %rbp
    167d:	48 8d 2d fc 26 00 00 	lea    0x26fc(%rip),%rbp        # 3d80 <__do_global_dtors_aux_fini_array_entry>
    1684:	53                   	push   %rbx
    1685:	4c 29 fd             	sub    %r15,%rbp
    1688:	48 83 ec 08          	sub    $0x8,%rsp
    168c:	e8 6f f9 ff ff       	callq  1000 <_init>
    1691:	48 c1 fd 03          	sar    $0x3,%rbp
    1695:	74 1f                	je     16b6 <__libc_csu_init+0x56>
    1697:	31 db                	xor    %ebx,%ebx
    1699:	0f 1f 80 00 00 00 00 	nopl   0x0(%rax)
    16a0:	4c 89 f2             	mov    %r14,%rdx
    16a3:	4c 89 ee             	mov    %r13,%rsi
    16a6:	44 89 e7             	mov    %r12d,%edi
    16a9:	41 ff 14 df          	callq  *(%r15,%rbx,8)
    16ad:	48 83 c3 01          	add    $0x1,%rbx
    16b1:	48 39 dd             	cmp    %rbx,%rbp
    16b4:	75 ea                	jne    16a0 <__libc_csu_init+0x40>
    16b6:	48 83 c4 08          	add    $0x8,%rsp
    16ba:	5b                   	pop    %rbx
    16bb:	5d                   	pop    %rbp
    16bc:	41 5c                	pop    %r12
    16be:	41 5d                	pop    %r13
    16c0:	41 5e                	pop    %r14
    16c2:	41 5f                	pop    %r15
    16c4:	c3                   	retq   
    16c5:	66 66 2e 0f 1f 84 00 	data16 nopw %cs:0x0(%rax,%rax,1)
    16cc:	00 00 00 00 

00000000000016d0 <__libc_csu_fini>:
    16d0:	f3 0f 1e fa          	endbr64 
    16d4:	c3                   	retq   

Disassembly of section .fini:

00000000000016d8 <_fini>:
    16d8:	f3 0f 1e fa          	endbr64 
    16dc:	48 83 ec 08          	sub    $0x8,%rsp
    16e0:	48 83 c4 08          	add    $0x8,%rsp
    16e4:	c3                   	retq   
