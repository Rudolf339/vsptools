import json, subprocess, sys, signal, time
from openvsp import vsp

with open('./runparams.json', 'r') as p:
    params = json.loads(p.read())

DRYRUN = False
CLEANUP = False
VERBOSE = False
HIGHRES = False
MEDRES = False
nproc = 1
wake = 3
progress = {
    "isused": "False",
    "done": "False",
    "dryrun": "False",
    "verbose": "False",
    "nproc": 2,
    "wake": 3,
    "completed": []
}
progressfile = 'progress.json'
for arg in sys.argv:
    if arg.startswith('-'):
        if 'd' in arg:
            DRYRUN = True
        if 'c' in arg:
            CLEANUP = True
        if 'v' in arg:
            VERBOSE = True
        if 'h' in arg:
            HIGHRES = True
        if 'm' in arg:
            MEDRES = True
    if arg.startswith('-j'):
        nproc = arg[2:]
    if arg.startswith('-w'):
        wake = arg[2:]
    if arg.startswith('--progressfile='):
        progressfile = arg[15:]
        with open(progressfile) as pf:
            progress = json.loads(pf.read())
        DRYRUN = progress['dryrun']
        CLEANUP = progress['cleanup']
        VERBOSE = progress['verbose']
        progress['isused'] = True

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

if not HIGHRES:
    mach = '0.2, 0.5, 0.9'
    if MEDRES:
        aoa = '-10.0, -5.0, 0.001, 5.0, 10.0, 15.0, 20.0,  25.0, 30.0, 40.0, 50.0, 60'
    else:
        aoa = '-10.0, 0.001, 10.0, 20.0, 30.0, 40.0, 50, 60'
    beta = '-10.0, 0.0, 10.0'

print('Mach:', mach + '!')
print('AoA:', aoa + '!')
print('Beta:', beta + '!')

baseprops = {"Sref": "45.692500",
             "Cref": "3.618333",
             "Bref": "14.540000",
             "X_cg": "1.846",
             "Y_cg": "0.000",
             "Z_cg": "0.000",
             "Mach": mach,
             "AoA": aoa,
             "Beta": beta,
             "Vinf": "100.000000",
             "Rho": "0.002377",
             "ReCref": "10000000.000000",
             "ClMax": params['CLmax']['base'],
             "MaxTurningAngle": "-1.000000",
             "Symmetry": "NO",
             "FarDist": "-1.000000",
             "NumWakeNodes": "0",
}
baseprops["WakeIters"] = str(wake)
configprops = {"base": {"NumberOfControlGroups": "0"}}

postprops = {"Preconditioner": "Matrix",
             "Karman-Tsien Correction": "Y"}

est_baseprops = dict()
for i in baseprops.keys():
    if i == 'Mach':
        est_baseprops['Mach'] = '0.4'
    elif i == 'AoA':
        est_baseprops['AoA'] = '5'
    elif i  == 'Beta':
        est_baseprops['Beta'] = '0'
    else:
        est_baseprops[i] = baseprops[i]

def interrupthandler(signal, frame):
    if progress['isused']:
        with open(progressfile, 'w+') as jf:
            jf.write(json.dumps(progress, sort_keys=True, indent=4))
        exit(0)

signal.signal(signal.SIGINT, interrupthandler)

def vprint(t):
    if VERBOSE:
        print(t)
def generate(loc, vspfile, name, manual=False, pos=0):
    # remove old outputs
    if name in params['surf_names']:
        name = params['surf_names'][name]
    subprocess.run(['rm', loc + 'A-6_DegenGeom.csv'])
    if not DRYRUN:
       subprocess.run(['rm', loc + 'A-6_DegenGeom.history'])
       if 'stab' in loc:
           subprocess.run(['rm', loc + 'A-6_DegenGeom.stab'])

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
    if VERBOSE:
        vsp.WriteVSPFile(loc + 'A-6_' + name + '.vsp3')
    vsp.ClearVSPModel()

    if CLEANUP:
        print('cleaning...')
        fn = loc + 'A-6_DegenGeom.'
        for ext in ['adb', 'adb.cases', 'fem', 'group.1', 'lod', 'polar']:
            subprocess.run(['rm', fn + ext])

print('Dryrun:', DRYRUN)
print('Cleanup:', CLEANUP)

for case in ['est', 'base', 'stab']:
    if params[case + '_file'] + params['vsp3_file'][:-5] not in progress['completed']:
        with open(params[case + '_file'] + 'A-6_DegenGeom.vspaero', 'w') as bf:
            for p in baseprops.keys():
                if case == 'est':
                    bf.write(p + ' = ' + est_baseprops[p] + ' \n')
                else:
                    bf.write(p + ' = ' + baseprops[p] + ' \n')
            for p in configprops['base'].keys():
                bf.write(p + ' = ' + configprops['base'][p] + ' \n')
            for p in postprops.keys():
                bf.write(p + ' = ' + postprops[p] + ' \n')

        # re-generate DegenGeom
        generate(params[case + '_file'], params['vsp3_file'], case)

        # run the solver
        if not DRYRUN or case == 'est':
            print('running: ' + case)
            if case == 'est':
                start_time = time.localtime()
            if case != 'stab':
                if VERBOSE:
                    subprocess.run(['bash', './run.sh', params[case + '_file'], nproc])
                else:
                    subprocess.run(['bash', './run.sh', params[case + '_file'], nproc],
                                   stdout=subprocess.DEVNULL)
            else:
                if VERBOSE:
                    subprocess.run(['bash', './runstab.sh', params[case + '_file'], nproc])
                else:
                    subprocess.run(['bash', './runstab.sh', params[case + '_file'], nproc],
                                   stdout=subprocess.DEVNULL)
            progress['completed'].append(params[case + '_file'] + params['vsp3_file'][:-5])

            # Calculate ETA
            if case == 'est':
                end_time = time.localtime()
                t = end_time.tm_hour - start_time.tm_hour
                t += (end_time.tm_min - start_time.tm_min) / 60
                t += (end_time.tm_sec - start_time.tm_sec) / 3600
                # number of cases:
                n = 7 # stability, base
                for i in params['files'].values():
                    n += len(i)
                n = n * len(baseprops['Mach'].split(', ')) * len(baseprops['AoA'].split(', ')) * len(baseprops['Beta'].split(', '))
                print('##### ETA: ' + str(round(t * n, 1)) + ' hours #####')

for run in params['files']:
    for case in params['files'][run]:
        if case + params['vsp3_file'][:-5] not in progress['completed']:
            output = []
            vsp_old = open(case + 'A-6_DegenGeom.vspaero', 'r')
            vsp_txt = vsp_old.readlines()
            vsp_old.close()
            for entry in baseprops.keys():
                if entry == 'ClMax' and run in params['CLmax']:
                    output.append(entry + " = " + params['CLmax'][run] + " \n")
                else:
                    output.append(entry + " = " + baseprops[entry] + " \n")
            for l in range(len(baseprops), len(vsp_txt)):
                output.append(vsp_txt[l])

            with open(case + 'A-6_DegenGeom.vspaero', 'w') as of:
                for t in output:
                    of.write(t)

            if run not in params['manual_set'].keys():
                generate(case, params['vsp3_file'], run)
            else:
                generate(case, params['vsp3_file'], params['manual_set'][run],
                         True, case.split('/')[len(case.split('/')) - 2])

            if not DRYRUN:
                print('running: ' + case)
                subprocess.run(['date'])
                if VERBOSE:
                    subprocess.run(['bash', './run.sh', case, nproc])
                else:
                    subprocess.run(['bash', './run.sh', case, nproc],
                                   stdout=subprocess.DEVNULL)

            progress['completed'].append(case + params['vsp3_file'][:-5])
print('FINISHED')
subprocess.run(['date'])
progress['done'] = True
with open(progressfile, 'w+') as jf:
    jf.write(json.dumps(progress, sort_keys=True, indent=4))
