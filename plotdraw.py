import matplotlib.pyplot as pyplot
import numpy, sys

wake_iterations = 3
data_order = ['Mach', 'AoA', 'beta', 'CL', 'CDo', 'CDi', 'CDtot', 'CS',
              'L/D', 'E', 'CFx', 'CFz', 'CFy', 'CMx', 'CMy', 'CMz', 'T/QS']
with open(sys.argv[1]) as f:
    input_txt = f.readlines()

db = []
try:
    interest = sys.argv[2]
except IndexError:
    interest = 'CL'

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

data = {'Mach': [], 'AoA': [], 'beta': [], 'CL': [], 'CDo': [], 'CDi': [],
        'CDtot': [], 'CS': [],'L/D': [], 'E': [], 'CFx': [], 'CFz': [],
        'CFy': [], 'CMx': [], 'CMy': [], 'CMz': [], 'T/QS': []}
for d in db:
    for k in d.keys():
        data[k].append(float(d[k]))

print(data)
pyplot.plot(data['AoA'], data[interest], label='CL')
pyplot.legend()
pyplot.show()
