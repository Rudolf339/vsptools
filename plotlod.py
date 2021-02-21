#!/usr/bin/env python3
import matplotlib.pyplot as pyplot
import sys
import json

wake_iterations = 3

TYPE = None
with open(sys.argv[1]) as f:
    if '.lod' in sys.argv[1]:
        TYPE = 'lod'
        data_order = ['wing', 'S', 'yavg', 'chord', 'v/vref', 'Cl', 'Cd', 'Cs',
                      'Cx', 'Cy', 'Cz', 'CMx', 'CMy', 'CMz']
        data_order_2 = ['comp', 'compname', 'Mach', 'AoA', 'beta', 'CL',
                        'CDi', 'CS', 'CFx', 'CFy', 'CFz', 'Cmx', 'Cmy', 'Cmz']
        data = {'wing': [], 'S': [], 'yavg': [], 'chord': [], 'v/vref': [],
                'Cl': [], 'Cd': [], 'Cs': [], 'compname': [], 'Mach': [], 'AoA': [], 'beta': [],
                'Cx': [], 'Cy': [], 'Cz': [], 'CMx': [], 'CMy': [], 'CMz': []}
        data_comp = {'comp': {}, 'compname': {}, 'Mach': {}, 'AoA': {},
                     'beta': {}, 'CL': {}, 'CDi': {}, 'CS': {}, 'CFx': {},
                     'CFy': {}, 'CFz': {}, 'Cmx': {}, 'Cmy': {}, 'Cmz': {}}
        X = 'yavg'
        Y = 'Cl'
    else:
        print('Incorrect filetype')
        exit()
    input_txt = f.readlines()

db = []
db_comp = []
AOA = [None]
MACH = [None]
BETA = [None]
WING = [None]
for arg in sys.argv:
    if arg.startswith('-x'):
        X = arg[2:]
    elif arg.startswith('-y'):
        Y = arg[2:]
    elif arg.startswith('-a'):
        AOA = [float(a) for a in arg[2:].split(',')]
    elif arg.startswith('-m'):
        MACH = [float(a) for a in arg[2:].split(',')]
    elif arg.startswith('-b'):
        BETA = [float(a) for a in arg[2:].split(',')]
    elif arg.startswith('-w'):
        WING = [int(a) for a in arg[2:].split(',')]


def getdata(line):
    while '  ' in line:
        line = line.replace('  ', ' ')
    line = line.split(' ')
    line2 = []
    for l in line:
        if l != '':
            line2.append(l)
    final = []
    for l in line2:
        try:
            final.append(float(l))
        except ValueError:
            if l != '':
                final.append(l)
    return line2


collect_w = False
collect_c = False
db_temp = []
db_comp_temp = []
for l in input_txt:
    if l == '\n':
        collect_w = False
        collect_c = False
        if db_temp != []:
            db.append(db_temp)
        if db_comp_temp != []:
            db_comp.append(db_comp_temp)
        db_temp = []
        db_comp_temp = []
    elif collect_w:
        dataset = {}
        for n in range(len(getdata(l[:-2]))):
            dataset[data_order[n]] = getdata(l)[n]
        db_temp.append(dataset)
    elif collect_c:
        dataset = {}
        for n in range(len(getdata(l[:-2]))):
            dataset[data_order_2[n]] = getdata(l)[n]
        db_comp_temp.append(dataset)
    elif l.startswith('   Wing'):
        collect_w = True
    elif l.startswith('Comp'):
        collect_c = True

with open('./debug.json', 'w+') as jf:
    jf.write(json.dumps(db, sort_keys=True, indent=4))

yres = dict()
xres = dict()
yall = []
xall = []
for i in range(len(db)):
    aoa = float(db_comp[i][0]['AoA'])
    beta = float(db_comp[i][0]['beta'])
    mach = float(db_comp[i][0]['Mach'])
    go = True
    if aoa not in AOA and None not in AOA:
        go = False
    if beta not in BETA and None not in BETA:
        go = False
    if mach not in MACH and None not in MACH:
        go = False
    if go:
        for d in db[i]:
            if int(d['wing']) in WING or None in WING:
                if d['wing'] not in yres:
                    wing_index = d['wing']
                    yres[wing_index] = list()
                    xres[wing_index] = list()
                yres[d['wing']].append(float(d[Y]))
                xres[d['wing']].append(float(d[X]))
                yall.append(float(d[Y]))
                xall.append(float(d[X]))
                txt = 'AoA=' + str(aoa).rstrip('0').rstrip('.')
                txt += ' beta=' + str(beta).rstrip('0').rstrip('.')
                txt += ' Mach=' + str(mach).rstrip('0').rstrip('.')
        if yres != []:
            for k in yres.keys():
                pyplot.plot(xres[k], yres[k],
                            label=(txt + ' wing=' +
                                   str(db_comp[i][int(k) - 1]['compname'])))

    yres = dict()
    xres = dict()


def nth(ls, n):
    out = []
    for i in range(len(ls)):
        if i % n == 0:
            out.append(ls[i])


N = 100
pyplot.xlabel(X)
pyplot.ylabel(Y)
# print(numpy.linspace(min(yall), max(yall) + 0.1, 10))
# pyplot.xticks(nth(xall, N))
# pyplot.yticks(nth(yall, N))
pyplot.legend()
pyplot.show()
