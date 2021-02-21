#!/usr/bin/env python3
import matplotlib.pyplot as pyplot
import numpy, sys

wake_iterations = 3

TYPE = None
with open(sys.argv[1]) as f:
    if '.history' in sys.argv[1]:
        TYPE = 'history'
        data_order = ['Mach', 'AoA', 'beta', 'CL', 'CDo', 'CDi', 'CDtot', 'CS',
                      'L/D', 'E', 'CFx', 'CFz', 'CFy', 'CMx', 'CMy', 'CMz', 'T/QS']
        data = {'Mach': [], 'AoA': [], 'beta': [], 'CL': [], 'CDo': [], 'CDi': [],
                'CDtot': [], 'CS': [],'L/D': [], 'E': [], 'CFx': [], 'CFz': [],
                'CFy': [], 'CMx': [], 'CMy': [], 'CMz': [], 'T/QS': []}
        X = 'AoA'
        Y = 'CL'
    elif '.lod' in sys.argv[1]:
        TYPE = 'lod'
        # data_order = ['wing', 'yavg', 'chord', 'Cl', 'Cd', 'Cs', 'compname',
        #               'Mach', 'AoA', 'beta', 'CL', 'CD', 'CS',
        #               'CFx', 'CFy', 'CFz', 'CMx', 'CMy', 'CMz']
        data_order = ['wing', 'S', 'yavg', 'chord', 'v/vref',
                'Cl', 'Cd', 'Cs', 'compname', 'Mach', 'AoA', 'beta',
                'Cx', 'Cy', 'Cz', 'CMx', 'CMy', 'CMz']
        data = {'wing': [], 'S': [], 'yavg': [], 'chord': [], 'v/vref': [],
                'Cl': [], 'Cd': [], 'Cs': [], 'compname': [], 'Mach': [], 'AoA': [], 'beta': [],
                'Cx': [], 'Cy': [], 'Cz': [], 'CMx': [], 'CMy': [], 'CMz': []}
        X = 'yavg'
        Y = 'Cl'
    else:
        print('Incorrect filetype')
        exit()
    input_txt = f.readlines()

db = []
AOA = None
MACH = None
BETA = None
WING = None
for arg in sys.argv:
    if arg.startswith('-x'):
        X = arg[2:]
    elif arg.startswith('-y'):
        Y = arg[2:]
    elif arg.startswith('-a'):
        AOA = float(arg[2:])
    elif arg.startswith('-m'):
        MACH = float(arg[2:])
    elif arg.startswith('-b'):
        BETA = float(arg[2:])
    elif arg.startswith('-w'):
        WING = float(arg[2:])


def getdata(line):
    while '  ' in line:
        line = line.replace('  ', ' ')
    line = line.split(' ')
    line2 = []
    for l in line:
        if l != '':
            line2.append(l)
    return line2

if TYPE == 'history':
    for i in range(len(input_txt)):
        if input_txt[i].startswith('Solver Case:'):
            l = i + 2 + wake_iterations
            t = input_txt[l].split(' ')
            while '' in t:
                t.remove('')
            t.remove(t[0])
            t[len(t) - 1] = t[len(t) - 1][:-1]
            dataset = {}
            for n in range(0, len(t)):
                data_name = data_order[n]
                dataset[data_name] = t[n]
            db.append(dataset)
else:
    collect_w = False
    collect_c = False
    for l in input_txt:
        if l == '\n':
            collect_w = False
            collect_c = False
        elif collect_w:
            dataset = {}
            for n in range(len(getdata(l[:-2]))):
                dataset[data_order[n]] = getdata(l)[n]
            db.append(dataset)
        elif l.startswith('   Wing'):
            collect_w = True
        elif l.startswith('Comp'):
            collect_c = True

for d in db:
    for k in d.keys():
        data[k].append(float(d[k]))

if TYPE == 'history':
    cases = {'AoA': [AOA, None], 'beta': [BETA, None], 'Mach': [MACH, None]}
elif TYPE == 'lod':
    cases = {'AoA': [AOA, None], 'beta': [BETA, None], 'Mach': [MACH, None], 'wing': [WING, None]}

def dataformater(inp, name):
    arr = set([a for a in data[name]])
    if inp is not None:
        arr = set([inp])
    return arr

for c in cases.keys():
    cases[c][1] = dataformater(cases[c][0], c)

def plotter(first, second, name1, name2):
    for f in first:
        for s in second:
            xres = []
            yres = []
            for i in range(len(data[X])):
                try:
                    if data[name2][i] == s or second == ['']:
                        two_is_good = True
                    else:
                        two_is_good = False
                except KeyError:
                    two_is_good = True
                if data[name1][i] == f and two_is_good:
                    yres.append(data[Y][i])
                    xres.append(data[X][i])
            if yres != []:
                if second == [''] or len(second) == 1:
                    pyplot.plot(xres, yres, label=name1 + '=' + str(f))
                else:
                    pyplot.plot(xres, yres, label=name1 + '=' + str(f)  + ' ' + name2 + '=' + str(s))
        if second is ['']:
            break

if X == 'AoA':
    plotter(cases['Mach'][1], cases['beta'][1], 'Mach', 'beta')
elif X == 'Mach':
    plotter(cases['Aoa'][1], cases['beta'][1], 'AoA', 'beta')
elif X == 'beta':
    plotter(cases['Aoa'][1], cases['Mach'][1], 'AoA', 'Mach')
elif TYPE == 'lod':
    print('lod')
    plotter(cases['wing'][1], [''], 'wing', '')

pyplot.xlabel(X)
pyplot.ylabel(Y)
pyplot.legend()
pyplot.show()
