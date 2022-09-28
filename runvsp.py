#!./vsp-venv/bin/python3
import json
import subprocess
import sys
import signal
import time
import argparse
from os import path
from openvsp import vsp

with open('./runparams.json', 'r') as p:
    params = json.loads(p.read())

parser = argparse.ArgumentParser()
parser.add_argument('--dryrun', '-d', help='Exectue without runnign vspaero', action='store_true')
parser.add_argument('--cleanup', '-c', help='Remove all files but .lod, .history and .stab', action='store_true')
parser.add_argument('--verbose', '-v', help='Increase verbosity', action='store_true')
parser.add_argument('--resolution', '-r', help='Set resolution of run', choices=['low', 'medium', 'high'], default='low')
parser.add_argument('--jobs', '-j', help='-omp setting of vspaero', default='1', type=str)
parser.add_argument('--wake', '-w', help='Number of wake iterations', default=3, type=int)
parser.add_argument('--force', '-f', help='Re-compute everything', action='store_true')
parser.add_argument('--ignore', '-i', help='Cases to skip, comma seperated', metavar='FOO,BAR')
parser.add_argument('--only', '-o', help='Only run these cases, comma seperated', metavar='FOO,BAR')
parser.add_argument('--progressfile', type=str)
args = parser.parse_args()

if args.ignore is not None and args.only is not None:
    print('Can\'t use --only and --ignore at the same time')
    exit()

if args.ignore is not None:
    ignore_list = args.ignore.split(',')
else:
    ignore_list = list()

if args.only is not None:
    only_list = args.only.split(',')
else:
    only_list = list()

wake = 3
progress = {
    "isused": "False",
    "done": "False",
    "dryrun": "False",
    "verbose": "False",
    "cleanup": "False",
    "nproc": 2,
    "wake": 3,
    "completed": []
}

# for arg in sys.argv:
#     if arg.startswith('-'):
#         if 'd' in arg:
#             DRYRUN = True
#         if 'c' in arg:
#             CLEANUP = True
#         if 'v' in arg:
#             VERBOSE = True
#         if 'h' in arg:
#             HIGHRES = True
#         if 'm' in arg:
#             MEDRES = True
#         if 'f' in arg:
#             FORCE = True
#     if arg.startswith('-j'):
#         nproc = arg[2:]
#     if arg.startswith('-w'):
#         wake = arg[2:]
#     if arg.startswith('--progressfile='):
#         progressfile = arg[15:]
if args.progressfile is not None:
    with open(args.progressfile) as pf:
        progress = json.loads(pf.read())
        # DRYRUN = progress['dryrun']
        # CLEANUP = progress['cleanup']
        # VERBOSE = progress['verbose']
        progress['isused'] = True
else:
    args.progressfile = 'progress.json'

if progress['completed'] == []:
    progress['done'] = False

mach = ""
aoa = ""
beta = "-20, -10, "

for m in range(1, 10):
    mach += str(m * 0.1)[0:3] + ", "
mach = mach[:len(mach) - 2]

for a in range(-10, 61, 5):
    aoa += str(a) + ", "
aoa = aoa[:len(aoa) - 2]

for b in range(-5, 6):
    beta += str(b) + ", "
beta = beta + "10, 20"

if args.resolution != 'high':
    mach = params['mach']
    if args.resolution == 'medium':
        aoa = params['aoa_medium']
        beta = params['beta_medium']
    else:
        aoa = params['aoa_low']
        beta = params['beta_low']

print('Mach:', mach + '!')
print('AoA:', aoa + '!')
print('Beta:', beta + '!')

baseprops = dict()
reserved_names = {'Mach': mach, 'AoA': aoa, 'Beta': beta,
                  'ClMax': params['CLmax']['base']}

with open(params['vspname']+'.vspaero', 'r') as v:
    for line in v:
        name = line.split(' ')[0]
        value = line.split(' ')[2]
        if name not in reserved_names:
            baseprops[name] = value
        else:
            baseprops[name] = reserved_names[name]
        if name == 'WakeIters':
            break

print(baseprops)
# baseprops = {"Sref": "49.14",
#              "Cref": "3.2569",
#              "Bref": "15.54",
#              "X_cg": "1.808",
#              "Y_cg": "0.000",
#              "Z_cg": "0.000",
#              "Mach": mach,
#              "AoA": aoa,
#              "Beta": beta,
#              "Vinf": "100.000000",
#              "Rho": "0.002377",
#              "ReCref": "10000000.000000",
#              "ClMax": params['CLmax']['base'],
#              "MaxTurningAngle": "-1.000000",
#              "Symmetry": "NO",
#              "FarDist": "-1.000000",
#              "NumWakeNodes": "0",
#              }

baseprops["WakeIters"] = str(args.wake)
configprops = {"base": {"NumberOfControlGroups": "0"}}

postprops = {"Preconditioner": "Matrix",
             "Karman-Tsien Correction": "N"}

est_baseprops = dict()
for i in baseprops.keys():
    if i == 'Mach':
        est_baseprops['Mach'] = '0.4'
    elif i == 'AoA':
        est_baseprops['AoA'] = '5'
    elif i == 'Beta':
        est_baseprops['Beta'] = '0'
    else:
        est_baseprops[i] = baseprops[i]


def interrupthandler(signal, frame):
    if progress['isused']:
        with open(args.progressfile, 'w+') as jf:
            jf.write(json.dumps(progress, sort_keys=True, indent=4))
        exit(0)


signal.signal(signal.SIGINT, interrupthandler)


def vprint(t):
    if args.verbose:
        print(t)


def generate(loc, vspfile, name, manual=False, pos=0):
    # check if dir exists, if not then create it
    if not path.exists(loc):
        subprocess.run(['mkdir', '-p', loc])
    # remove old outputs
    if name in params['surf_names']:
        name = params['surf_names'][name]
    subprocess.run(['rm', loc + params['vspname'] + '.csv'])
    if not args.dryrun and False:
        subprocess.run(['rm', loc + params['vspname'] + '.history'])
        if 'stab' in loc:
            subprocess.run(['rm', loc + params['vspname'] + '.stab'])

    # generate new vspaero input
    vsp.ReadVSPFile(vspfile)
    vsp.SetVSP3FileName(loc + vspfile)

    # edit model if necessary
    if manual:
        print(name)
        geom_id = vsp.FindGeomsWithName(name)[0]
        for p in vsp.GetGeomParmIDs(geom_id):
            if vsp.GetParmName(p) == 'Y_Rotation':
                print('rotating by', pos)
                vsp.SetParmVal(p, float(pos))
                break
        for n in vsp.GetAllSubSurfIDs():
            vsp.DeleteSubSurf(n)
    else:
        for n in vsp.GetAllSubSurfIDs():
            if name != vsp.GetSubSurfName(n):
                vsp.DeleteSubSurf(n)
            else:
                vprint(name + ' ' + vsp.GetSubSurfName(n))

    print('witing out', loc + vspfile[:-5] + '_DegenGeom.csv')
    vsp.ComputeDegenGeom(vsp.SET_ALL, vsp.DEGEN_GEOM_CSV_TYPE)
    vsp.WriteVSPFile(loc + params['vspname'] + name + '.vsp3')
    vsp.ClearVSPModel()

    if args.cleanup:
        print('cleaning...')
        fn = loc + params['vspname'] + '.'
        for ext in ['adb', 'adb.cases', 'fem', 'group.1', 'lod', 'polar']:
            subprocess.run(['rm', fn + ext])


print('Dryrun:', args.dryrun)
print('Cleanup:', args.cleanup)
STARTTIME = time.localtime()

for case in ['est', 'base', 'stab']:
    if case != 'est' and (case in ignore_list or (only_list != list() and
                                                  case not in only_list)):
        continue
    if (params[case + '_file'] + params['vsp3_file'][:-5]
            not in progress['completed']):
        # check if dir exists, else create
        if not path.exists(params[case + '_file']):
            subprocess.run(['mkdir', '-p', params[case + '_file']])
        nochange = True
        try:
            with open(params[case + '_file'] + params['vspname'] + '.vspaero') as f:
                old = f.readlines()
        except FileNotFoundError:
            old = None
        with open(params[case + '_file'] + params['vspname'] + '.vspaero', 'w') as bf:
            for p in baseprops.keys():
                if p == 'ClMax' and case in params['CLmax']:
                    bf.write(p + " = " + params['CLmax'][case] + " \n")
                if case == 'est':
                    bf.write(p + ' = ' + est_baseprops[p] + ' \n')
                else:
                    bf.write(p + ' = ' + baseprops[p] + ' \n')
            for p in configprops['base'].keys():
                bf.write(p + ' = ' + configprops['base'][p] + ' \n')
            for p in postprops.keys():
                bf.write(p + ' = ' + postprops[p] + ' \n')

        with open(params[case + '_file'] + params['vspname'] + '.vspaero') as f:
            new = f.readlines()
        if new != old:
            nochange = False

        try:
            with open(params[case + '_file'] + params['vspname'] + '.csv') as f:
                old = f.readlines()
        except FileNotFoundError:
            old = None
        # re-generate DegenGeom
        if case != 'stab' or True: # TODO
            vsp3 = params['vsp3_file']
        else:
            vsp3 = params['stab_vsp3_file']
        generate(params[case + '_file'], vsp3, case)
        with open(params[case + '_file'] + params['vspname'] + '.csv') as f:
            new = f.readlines()
        if new != old or case == 'est':
            nochange = False

        if not nochange or args.force:
            # run the solver
            if not args.dryrun or case == 'est':
                print('running: ' + case)
                if case == 'est':
                    start_time = time.localtime()
                subprocess.run(['date'])
                if case != 'stab':
                    subprocess.run(['bash', './run.sh', params[case + '_file'], args.jobs, '0'],
                                   stdout=subprocess.DEVNULL)
                else:
                    subprocess.run(['bash', './runstab.sh', params[case + '_file'], args.jobs, '0'],
                                   stdout=subprocess.DEVNULL)
                progress['completed'].append(params[case + '_file'] + params['vsp3_file'][:-5])

                # Calculate ETA
                if case == 'est':
                    end_time = time.localtime()
                    t = end_time.tm_hour - start_time.tm_hour
                    t += (end_time.tm_min - start_time.tm_min) / 60
                    t += (end_time.tm_sec - start_time.tm_sec) / 3600
                    # number of cases:
                    n = 7  # stability, base
                    for i in params['files'].values():
                        n += len(i)
                    n = n * len(baseprops['Mach'].split(', ')) * len(baseprops['AoA'].split(', ')) * len(baseprops['Beta'].split(', '))
                    ETA = round(t * n, 1)
                    print('##### ETA:', ETA, 'hours #####')
        else:
            print(case, 'needed no re-compute')

for run in params['files']:
    if run in ignore_list or (only_list != list() and run not in only_list):
        continue
    for case in params['files'][run]:
        if case + params['vsp3_file'][:-5] not in progress['completed']:
            output = []
            try:
                with open(case + params['vspname'] + '.vspaero', 'r') as vsp_old:
                    vsp_txt = vsp_old.readlines()
            except FileNotFoundError:
                subprocess.run(['cp', params['vspname']+'.vspaero',
                                case + params['vspname'] + '.vspaero'])
                with open(case + params['vspname'] + '.vspaero', 'r') as vsp_old:
                    vsp_txt = vsp_old.readlines()
            for entry in baseprops.keys():
                if entry == 'ClMax' and run in params['CLmax']:
                    output.append(entry + " = " + params['CLmax'][run] + " \n")
                elif entry == 'Beta' and run in params['alpha_only']:
                    output.append('Beta = 0 \n')
                else:
                    output.append(entry + " = " + baseprops[entry] + " \n")
            for l in range(len(baseprops), len(vsp_txt)):
                output.append(vsp_txt[l])

            nochange = True
            try:
                with open(case + params['vspname'] + '.vspaero') as f:
                    old = f.readlines()
            except FileNotFoundError:
                old = None
            with open(case + params['vspname'] + '.vspaero', 'w') as of:
                for t in output:
                    of.write(t)
            with open(case + params['vspname'] + '.vspaero') as f:
                new = f.readlines()
            if new != old:
                nochange = False

            try:
                with open(case + params['vspname'] + '.csv') as f:
                    old = f.readlines()
            except FileNotFoundError:
                old = None
            if run not in params['manual_set'].keys():
                generate(case, params['vsp3_file'], run)
            else:
                generate(case, params['vsp3_file'], params['manual_set'][run],
                         True, case.split('/')[len(case.split('/')) - 2])
            with open(case + params['vspname'] + '.csv') as f:
                new = f.readlines()
            if new != old:
                nochange = False
            if not nochange or args.force:
                if not args.dryrun:
                    print('running: ' + case)
                    subprocess.run(['date'])
                    if 'ground_effect' in case:
                        agl = case.split('/')[-2]
                        print('agl:', agl)
                    else:
                        agl = '0'
                    subprocess.run(['bash', './run.sh', case, args.jobs, agl],
                                   stdout=subprocess.DEVNULL)
            else:
                print(case, 'needed no re-compute')
            progress['completed'].append(case + params['vsp3_file'][:-5])
print('FINISHED')
subprocess.run(['date'])
print('ETA was:', ETA, 'hours')
progress['done'] = True
end_time = time.localtime()
t = end_time.tm_hour - start_time.tm_hour
t += (end_time.tm_min - start_time.tm_min) / 60
t += (end_time.tm_sec - start_time.tm_sec) / 3600
print('Actual processing time:', round(t, 1), 'hours')
with open(args.progressfile, 'w+') as jf:
    jf.write(json.dumps(progress, sort_keys=True, indent=4))
