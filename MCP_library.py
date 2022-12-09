import numpy as np
import math
from pandas import read_csv as pdread
# import pandas as pd
import datetime
from os import path


# Reads .pos file and extracts scan parameters
class Pos:

    def __init__(self,
                 filename,
                 ke_pts=0,
                 ke_arr=None,
                 nest_pts=1,
                 nest_arr=None,
                 hv_pts=0,
                 hv_arr=None,
                 t_start=np.nan,
                 is_snapshot=False,
                 is_nested=False,
                 is_nexafs=False):
        self.filename = filename
        self.ke_pts = ke_pts
        self.ke_arr = ke_arr
        self.nest_pts = nest_pts
        self.nest_arr = nest_arr
        self.hv_pts = hv_pts
        self.hv_arr = hv_arr
        self.t_start = t_start
        self.is_snapshot = is_snapshot
        self.is_nested = is_nested
        self.is_nexafs = is_nexafs

        file_n = path.splitext(filename)[0]
        if file_n.endswith('_A') or file_n.endswith('_B'):
            file_n = file_n.replace('_A', '').replace('_B', '')
        pos_file = file_n + '.pos'

        head = list()
        nest = ''
        kin_ene = ''
        t_start = ''
        hv_ene = ''

        with open(pos_file) as f:
            for i, line in enumerate(f):
                if line.startswith('	// Manipulator (R1)// Scan ') or line.startswith('	// Delay// Scan '):
                    nest += line.replace('	// Manipulator (R1)// Scan ',
                                         '').replace('	// Delay// Scan ', '').replace('\n', '').replace('[', '')
                    self.is_nested = True
                elif line.startswith('	// Scan started at: '):
                    t_start += line.replace('	// Scan started at: ', '').replace('\n', '').replace('[', '')
                elif line.startswith('	// Energy// Scan  '):
                    kin_ene += line.replace('	// Energy// Scan  ', '').replace('\n', '').replace('[', '')
                elif line.startswith('Hv_Ene// Scan '):
                    hv_ene += line.replace('Hv_Ene// Scan ', '').replace('\n', '').replace('[', '')
                elif line.startswith('// '):
                    head.append(line)
                elif line.startswith('//////') and i > 0:
                    break

        # Remove heading slashes, spaces and newline
        head = [e.replace('// ', '') for e in head]
        head = [e.replace(' ', '') for e in head]
        head = [e.replace('\n', '') for e in head]

        # Split list into pairs
        head = [e.split(':', 1) for e in head]

        # Create dictionary for metadata
        meta = {k: v for k, v in head}

        # Set key types
        '''float_keys = ['R1', 'Xm', 'Ym', 'Zm', 'PassEnergy', 'DetectorVoltage', 'DLDVoltage']
        for k, v in meta.items():
            if k in float_keys:
                meta[k] = float(v)

        del meta['Analyzersettings']'''

        self.meta = meta

        # Read scan parameters and creates scan arrays
        if t_start:
            self.t_start = float(t_start)

        nest = nest.split(']')
        nest.pop(-1)
        nest = [n.split(',') for n in nest]

        nest_pars = np.zeros((len(nest), 4))
        for i, line in enumerate(nest):
            nest_pars[i] = [float(num) for num in line]

        self.nest_pts = sum([int((a[1] - a[0]) / a[2]) + 1 for a in nest_pars]) if self.is_nested else 1

        nest_arr = []
        for a in nest_pars:
            nest_arr = np.append(nest_arr, np.arange(a[0], a[1] + a[2], a[2]))
        self.nest_arr = nest_arr

        kin_ene = kin_ene.split(']')
        kin_ene.pop(-1)
        kin_ene = [n.split(',') for n in kin_ene]

        kin_ene_pars = np.zeros((len(kin_ene), 4))
        for i, line in enumerate(kin_ene):
            kin_ene_pars[i] = [float(num) for num in line]

        self.ke_pts = sum([int((a[1] - a[0]) / a[2]) + 1 for a in kin_ene_pars])

        hv_ene = hv_ene.split(']')
        hv_ene.pop(-1)
        hv_ene = [n.split(',') for n in hv_ene]

        hv_ene_pars = np.zeros((len(hv_ene), 4))
        for i, line in enumerate(hv_ene):
            hv_ene_pars[i] = [float(num) for num in line]
        self.hv_pts = sum([int((a[1] - a[0]) / a[2]) + 1 for a in hv_ene_pars])
        if self.hv_pts > 0:
            self.is_nexafs = True

        hv_arr = []
        for a in hv_ene_pars:
            hv_arr = np.append(hv_arr,
                               np.arange(a[0], a[1], a[2]))  # l'ultimo punto nelle regioni NEXAFS non viene fatto
        self.hv_arr = hv_arr

        ke_arr = []
        for a in kin_ene_pars:
            ke_arr = np.append(ke_arr, np.arange(a[0], a[1] + a[2], a[2]))
            if a[2] >= 1:
                self.is_snapshot = True
        if self.is_snapshot and self.nest_pts > 1:
            self.ke_arr = [np.append(ke_arr, ke_arr)[0] for _ in range(self.nest_pts)]
        elif self.is_nexafs:
            self.ke_arr = [np.append(ke_arr, ke_arr)[0] for _ in range(self.hv_pts)]  # nest_arr]
        else:
            self.ke_arr = ke_arr

        return


# Opens and extracts spectra from PrX
class Prx:

    def __init__(self,
                 filename,
                 step=0.1,
                 ch_start=0,
                 ch_end=2000,
                 photon=0.):
        self.filename = filename

        file_n = path.splitext(filename)[0]
        file_prx = file_n + '.PrX'
        # Set constants
        mcp_len = ch_end - ch_start

        date = datetime.datetime.strptime(path.basename(file_n)[0:10], '%d_%m_%Y').date()
        mcp_change_date = datetime.date(2018, 3, 18)
        if date > mcp_change_date:
            mcp2ke = 14300
        else:
            mcp2ke = 7320

        # Load the file
        data = pdread(file_prx, sep='\t', header=None).to_numpy(dtype=np.float64)

        print('Extracting data:', path.basename(file_prx))

        ke_arr = data[..., 0]
        pe_arr = data[..., 1]
        if data.shape[1] - 2 < mcp_len:
            mcp = data[..., 2:]
            mcp_len = data.shape[1] - 2
            ch_start = 0
            ch_end = mcp_len
        else:
            mcp = data[..., ch_start + 2:ch_end + 2]

        self.mcp1 = mcp
        self.para = [mcp2ke, mcp_len, ch_start, ch_end]

        print('Ch/eV @ PE1 =', str(mcp2ke))
        print('Mcp length =', str(mcp_len))

        pos = Pos(filename)

        if not np.where(np.diff(ke_arr) < 0)[0].size > 0:
            scan_len = ke_arr.size
        else:
            scan_len = int(np.where(np.diff(ke_arr) < 0)[0][0] + 1)
        if pos.is_nexafs:
            scan_num = int(pos.hv_pts)
            scan_len = int(pos.nest_pts)
        elif pos.is_snapshot and not pos.is_nexafs:
            scan_num = int(pos.nest_pts)
            scan_len = int(len(pos.ke_arr) / pos.nest_pts)
        else:
            scan_num = int(np.where(np.diff(ke_arr) < 0)[0].size + 1)

        missing_pts = (scan_len * scan_num) - ke_arr.size
        if missing_pts > 0:
            mcp = np.append(mcp, np.zeros((missing_pts, mcp_len), dtype=float), axis=0)
            ke_arr = np.append(ke_arr, pos.ke_arr[-missing_pts:])
            pe_arr = np.append(pe_arr, np.full(missing_pts, pe_arr[0]))
            print('There are ' + str(missing_pts) + ' missing points')

        mcp_cube = np.reshape(mcp, (int(mcp.shape[0] / scan_len), scan_len, mcp_len))
        # ke_arr_2d = np.reshape(ke_arr, (int(mcp.shape[0]/scan_len), scan_len)) not necessary ATM

        pass_ene = pe_arr[0]
        # Calculate MCP offsets
        mcp_offset = ((ke_arr - ke_arr[0]) * mcp2ke / pe_arr).astype(int)

        # Calculate sum over MCP
        shape = (int(mcp.shape[0] / scan_len), mcp_offset.max() + mcp_len)
        mcp_sum = np.zeros(shape)

        for i, layer in enumerate(mcp_cube):
            for j, row in enumerate(layer):
                mcp_sum[i, mcp_offset[j]:mcp_offset[j] + mcp_len] += row

        # Calculate kinetic energy
        central_bin = int((data.shape[1] - 2)/2)
        ke_start = ke_arr[0] - (central_bin - ch_start) * pass_ene / mcp2ke
        ke_stop = ke_arr[scan_len - 1] + (ch_end - central_bin) * pass_ene / mcp2ke
        ke_sum = np.linspace(ke_start, ke_stop, mcp_sum[0].size)

        # Down-sample to step size, padding arrays to required dimension for the averaging.
        R = int(mcp2ke * step / pass_ene)
        pad_size = math.ceil(float(mcp_sum[0].size) / R) * R - mcp_sum[0].size
        spectrum = np.zeros((int(mcp.shape[0] / scan_len), math.ceil(float(mcp_sum[0].size) / R)))
        ke = np.zeros((int(mcp.shape[0] / scan_len), math.ceil(float(mcp_sum[0].size) / R)))

        for i, row in enumerate(mcp_sum):
            mcp_sum_padded = np.append(row, np.zeros(pad_size) * np.NaN)
            spectrum[i] = np.nanmean(mcp_sum_padded.reshape(-1, R), axis=1)

            ke_sum_padded = np.append(ke_sum, np.zeros(pad_size) * np.NaN)
            ke[i] = np.nanmean(ke_sum_padded.reshape(-1, R), axis=1)

        self.e_bin = ke - photon
        self.spectrum_2d = spectrum
        self.spectrum_1d = np.sum(spectrum, axis=0)
        self.e_kin = ke[0]
        self.pass_ene = pe_arr

        return


# Opens .intx to extract for nested array
class Intx:

    def __init__(self,
                 filename,
                 nest_arr=None,
                 scan_num=0,
                 trx_a=None,
                 trx_b=None,
                 nexafs_multi=None,
                 hv_ene=None,
                 kin_ene=None):
        self.filename = filename
        self.nest_arr = nest_arr
        self.scan_num = scan_num
        self.trx_a = trx_a
        self.trx_b = trx_b
        self.nexafs_multi = nexafs_multi
        self.hv_ene = hv_ene
        self.kin_ene = kin_ene

        file_n = path.splitext(filename)[0]
        if file_n.endswith('_A') or file_n.endswith('_B'):
            file_n = file_n.replace('_A', '').replace('_B', '')
        intx_file = file_n + '.intx'

        if path.exists(intx_file):
            meta = list()
            with open(intx_file) as f:
                for i, line in enumerate(f):
                    if line.startswith('*******'):
                        start_index = i
                        break
                    meta.append(line.replace('\n', '').replace(' ', ''))

            col_name = meta[start_index - 2].split('\t')
            data_int = pdread(intx_file, sep='\t', header=None, names=col_name,
                              skiprows=list(range(0, start_index + 1))).to_numpy(dtype=np.float64)

            nest_arr = data_int[..., 0]
            t_start = Pos(filename).t_start
            if nest_arr[0] == 0 and not np.isnan(t_start):
                nest_arr += t_start
            self.nest_arr = nest_arr

            if 'nexA' and 'nexB' in col_name:
                self.trx_a = data_int[..., 3]
                self.trx_b = data_int[..., 4]
                self.nexafs_multi = data_int[..., -1]

            if 'kin_ene' in col_name:
                self.kin_ene = data_int[..., 1]
            elif 'hv_ene' in col_name:
                self.hv_ene = data_int[..., 1]

            self.scan_num = np.where(np.diff(self.nest_arr) != 0)[0].size + 1

        return


class Int:

    def __init__(self,
                 filename):

        self.filename = filename

        file_n = path.splitext(filename)[0]
        if file_n.endswith('_A') or file_n.endswith('_B'):
            file_n = file_n.replace('_A', '').replace('_B', '')
        int_file = file_n + '.int'

        data = pdread(int_file, sep='\t', header=None).to_numpy(dtype=np.float64)

        nexafs = data[..., 2]
        hv_ene = data[..., 1]
        nest = data[..., 0]

        if np.where(np.diff(hv_ene) < 0)[0].size > 0:
            scan_len = int(np.where(np.diff(hv_ene) < 0)[0][0] + 1)
            is_nested = True
        else:
            scan_len = len(hv_ene)
            is_nested = False

        zeros = np.insert(np.where(np.diff(hv_ene) < 0)[0] + 1, 0, 0)
        if is_nested:
            nest = nest[zeros]
            hv_ene = hv_ene[0:zeros[1]]

        self.nexafs = nexafs
        self.nest = nest
        self.hv_ene = hv_ene
        self.scan_len = scan_len

        return
