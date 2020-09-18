import json, subprocess, sys
from openvsp import vsp

nproc = sys.argv[1]

DRYRUN = False
CLEANUP = False

for arg in sys.argv:
    if arg.startswith('-'):
        if 'd' in arg:
            DRYRUN = True
        if 'c' in arg:
            CLEANUP = True

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

mach = '0.2, 0.5, 0.9'
aoa = '-10.0, -5.0, 0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40'
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
             "ClMax": "0.6",
             "MaxTurningAngle": "-1.000000",
             "Symmetry": "NO",
             "FarDist": "-1.000000",
             "NumWakeNodes": "0",
             "WakeIters": "3"
}

configprops = {"base": {"NumberOfControlGroups": "0"}}

postprops = {"Preconditioner": "Matrix",
             "Karman-Tsien Correction": "Y"}

def generate(loc, vspfile, manual=False, name='', pos=0):
    # remove old outputs
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
            if vsp.GetParmName(p) == 'Y_Rotations':
                vsp.SetParmVal(p, pos)
                break
    print('witing out', loc + vspfile + '.csv')
    vsp.ComputeDegenGeom(vsp.SET_ALL, vsp.DEGEN_GEOM_CSV_TYPE)
    vsp.ClearVSPModel()

    if CLEANUP:
        print('cleaning...')
        fn = loc + 'A-6_DegenGeom.'
        for ext in ['adb', 'adb.cases', 'csv',
                    'fem', 'group.1', 'lod', 'polar']:
            subprocess.run(['rm', fn + ext])

with open('./runparams.json', 'r') as p:
    params = json.loads(p.read())

for case in ['base', 'stab']:
    with open(params[case + '_file'] + 'A-6_DegenGeom.vspaero', 'w') as bf:
        for p in baseprops.keys():
            bf.write(p + ' = ' + baseprops[p] + ' \n')
        for p in configprops['base'].keys():
            bf.write(p + ' = ' + configprops['base'][p] + ' \n')
        for p in postprops.keys():
            bf.write(p + ' = ' + postprops[p] + ' \n')

    # re-generate DegenGeom
    generate(params[case + '_file'], params['vsp3_file'])
    
    # run the solver
    if not DRYRUN:
        print('running: ' + case)
        subprocess.run(['date'])
        if case == 'base':
            subprocess.run(['bash', './run.sh', params[case + '_file'], nproc], stdout=subprocess.DEVNULL)
        else:
            subprocess.run(['bash', './runstab.sh', params[case + '_file'], nproc], stdout=subprocess.DEVNULL)

for run in params['files']:
    for case in params['files'][run]:
        output = []
        vsp_old = open(case + 'A-6_DegenGeom.vspaero', 'r')
        vsp_txt = vsp_old.readlines()
        vsp_old.close()
        for entry in baseprops.keys():
            output.append(entry + " = " + baseprops[entry] + " \n")
        for l in range(len(baseprops), len(vsp_txt)):
            output.append(vsp_txt[l])

        with open(case + 'A-6_DegenGeom.vspaero', 'w') as of:
            for t in output:
                of.write(t)

        if run not in params['manual_set'].keys():
            generate(case, params['vsp3_file'])
        else:
            generate(case, params['vsp3_file'], True, params['manual_set'][run],
                     case.split('/')[len(case.split('/')) - 2])
        
        if not DRYRUN:
            print('running: ' + case)
            subprocess.run(['date'])
            subprocess.run(['bash', './run.sh', case], stdout=subprocess.DEVNULL)

print('FINISHED')
subprocess.run(['date'])
