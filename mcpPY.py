import MCP_library as mcp
import os
import sys
from igorwriter import IgorWave5
from os import path

# fdir = path.abspath(path.join(path.dirname(__file__), 'I_O'))
fdir = (path.dirname(sys.argv[0],) + os.sep + 'I_O').replace("/", "\\")# Get the current working directory (cwd)
files = os.listdir(fdir)  # Get all the files in that directory

for f in files:
    if f != 'Igor_cmd.txt':
        os.remove(fdir+'\\'+f)

os.chdir(fdir)

print(fdir)
print('Doing some magic...')
with open('igor_cmd.txt', 'r') as cmd:
    for i, line in enumerate(cmd):
        if line.startswith('	"filename '):
            filename = line.replace('	"filename ', '').replace('\n', '').replace("\"", "").replace('\\\\', '\\')
        elif line.startswith('	"step '):
            step = float(line.replace('	"step ', '').replace('\n', '').replace('\"', ''))
        elif line.startswith('	"ch_start '):
            ch_start = int(line.replace('	"ch_start ', '').replace('\n', '').replace('\"', ''))
        elif line.startswith('	"ch_end '):
            ch_end = int(line.replace('	"ch_end ', '').replace('\n', '').replace('\"', ''))
        elif line.startswith('	"photon '):
            photon = float(line.replace('	"photon ', '').replace('\n', '').replace('\"', ''))

'''
filename = "\\\\192.168.33.8\\Data\\2019\\Jun\\02_06_2019\\02_06_201901_A.PrX"
step = 0.05
ch_start = 0
ch_end = 800
photon = 1
'''
# open files and generate spectra + axes
pos = mcp.Pos(filename)
intx = mcp.Intx(filename)

file_n = mcp.path.splitext(filename)[0]
if file_n.endswith('_A') or file_n.endswith('_B'):
    file_n = file_n.replace('_A', '').replace('_B', '')
    prx_a = mcp.Prx((file_n + '_A.PrX'), photon=photon, step=step, ch_start=ch_start, ch_end=ch_end)
    prx_b = mcp.Prx((file_n + '_B.PrX'), photon=photon, step=step, ch_start=ch_start, ch_end=ch_end)
    filename = file_n + '.PrX'
else:
    prx_a = None
    prx_b = None

prx = mcp.Prx(filename, photon=photon, step=step, ch_start=ch_start, ch_end=ch_end)

scan_mat = mcp.np.mat(prx.spectrum_2d)
counts = prx.spectrum_1d
e_kin = prx.e_kin
e_bin = prx.e_bin
nest = pos.nest_arr
hv_ene = pos.hv_arr

# Save mat_mcp as Igor Binary
IgorWave5(prx.mcp1, name='mcp0').save('mat_mcp')

IgorWave5(prx.para, name='para0').save('para')

# save basic output files

IgorWave5(scan_mat, name='mat2d0').save('mat2d')
IgorWave5(counts, name='counts0').save('counts')
IgorWave5(e_kin, name='kin_ene0').save('e_kin')
# IgorWave5(e_bin, name='e_bin0').save('counts')
IgorWave5(prx.pass_ene[0:9], name='pass_ene0').save('pass_ene')


if len(nest) > 1:
    IgorWave5(nest, name='nest0').save('nest')

# save a,b, and a-b
if prx_a:
    mat_a = mcp.np.mat(prx_a.spectrum_2d)
    mat_b = mcp.np.mat(prx_b.spectrum_2d)
    mat_c = mat_a - mat_b
    scan_a = prx_a.spectrum_1d
    scan_b = prx_b.spectrum_1d
    scan_c = scan_a - scan_b

    IgorWave5(mat_a, name='mat2d_a0').save('mat2d_a')
    IgorWave5(mat_b, name='mat2d_b0').save('mat2d_b')
    IgorWave5(mat_c, name='mat2d_c0').save('mat2d_c')

    IgorWave5(scan_a, name='counts_a0').save('counts_a')
    IgorWave5(scan_b, name='counts_b0').save('counts_b')
    IgorWave5(scan_c, name='counts_c0').save('counts_c')


if pos.is_nested and not mcp.np.isnan(pos.t_start):
    scan_neg = mcp.np.repeat(mcp.np.mean(scan_mat[0:5, ...], axis=0), scan_mat.shape[0], axis=0)
    scan_norm = scan_mat - scan_neg
    IgorWave5(scan_norm, name='mat2d_n0').save('mat2d_n')


if pos.is_nexafs:
    nex = mcp.Int(filename)
    nex_cts = nex.nexafs
    hv_ene = nex.hv_ene
    IgorWave5(nex_cts, name='nex0').save('nex')
    IgorWave5(hv_ene, name='hv_ene0').save('hv_ene')

    if pos.is_nested and not prx_a:
        nest = nex.nest
        if nest.any():
            IgorWave5(nest, name='nest0').save('nest')
        nex2d = mcp.np.mat(mcp.np.reshape(nex_cts, (len(nest), len(hv_ene)))).T
        IgorWave5(nest, name='nex2d0').save('nex2d')

    if pos.is_nested and prx_a:
        nex_a = intx.trx_a
        nex_b = intx.trx_b
        nex2d_a = mcp.np.mat(mcp.np.reshape(nex_a, (len(nex.nest), len(hv_ene)))).T
        nex2d_b = mcp.np.mat(mcp.np.reshape(nex_b, (len(nex.nest), len(hv_ene)))).T
        nex2d_c = nex2d_a - nex2d_b

        IgorWave5(nex2d_a, name='nex2d_a0').save('nex2d_a')
        IgorWave5(nex2d_b, name='nex2d_b0').save('nex2d_b')
        IgorWave5(nex2d_c, name='nex2d_c0').save('nex2d_c')
        if nest.any():
            IgorWave5(nest, name='nest0').save('nest')

    if prx_a and not pos.is_nested:
        nex_a = intx.trx_a
        nex_b = intx.trx_b
        nex_c = nex_a - nex_b
        hv_ene = intx.hv_ene
        nex_multi = intx.nexafs_multi

        IgorWave5(nex_a, name='nex_a0').save('nex_a')
        IgorWave5(nex_b, name='nex_b0').save('nex_b')
        IgorWave5(nex_c, name='nex_c0').save('nex_c')
        IgorWave5(nex_multi, name='nex_multi0').save('nex_multi')
