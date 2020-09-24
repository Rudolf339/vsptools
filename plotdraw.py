import matplotlib.pyplot as pyplot
import numpy, sys

wake_iterations = 3
data_order = ['Mach', 'AoA', 'beta', 'CL', 'CDo', 'CDi', 'CDtot', 'CS',
              'L/D', 'E', 'CFx', 'CFz', 'CFy', 'CMx', 'CMy', 'CMz', 'T/QS']

with open(sys.argv[1]) as f:
    if '.history' in sys.argv[1]:
        TYPE = 'history'
    elif '.lod' in sys.argv[1]:
        TYPE = 'lod'
    input_txt = f.readlines()

db = []

X = 'AoA'
Y = 'CL'
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

for i in range(len(input_txt)):
    if input_txt[i].startswith('Solver Case:') and TYPE == 'history':
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

data = {'Mach': [], 'AoA': [], 'beta': [], 'CL': [], 'CDo': [], 'CDi': [],
        'CDtot': [], 'CS': [],'L/D': [], 'E': [], 'CFx': [], 'CFz': [],
        'CFy': [], 'CMx': [], 'CMy': [], 'CMz': [], 'T/QS': []}
for d in db:
    for k in d.keys():
        data[k].append(float(d[k]))

aoa = set([a for a in data['AoA']])
if AOA is not None:
    if AOA in aoa:
        aoa = set([AOA])
    else:
        print('Input AOA did not occure in input file')
        exit

mach = set([a for a in data['Mach']])
if MACH is not None:
    if MACH in mach:
        mach = set([MACH])
    else:
        print('Input Mach did not occure in input file')
        exit

beta = set([a for a in data['beta']])
if BETA is not None:
    if BETA in beta:
        beta = set([BETA])
    else:
        print('Input beta did not occure in input file')
        exit

print(X, Y, AOA, MACH, BETA)
print(aoa, mach, beta)

def plotter(first, second, name1, name2):
    for f in first:
        for s in second:
            xres = []
            yres = []
            for i in range(len(data[X])):
                if data[name1][i] == f and data[name2][i] == s:
                    yres.append(data[Y][i])
                    xres.append(data[X][i])
            if yres != []:
                pyplot.plot(xres, yres, label=name1 + '=' + str(f)  + ' ' + name2 + '=' + str(s))

if X == 'AoA':
    plotter(mach, beta, 'Mach', 'beta')
elif X == 'Mach':
    plotter(aoa, beta, 'AoA', 'beta')
elif X == 'beta':
    plotter(aoa, mach, 'AoA', 'Mach')

pyplot.xlabel(X)
pyplot.ylabel(Y)
pyplot.legend()
pyplot.show()
