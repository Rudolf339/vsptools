# Calculate engine milthrust table based on
# CL, CDtot, max speed and acceleration figures
# Jüttner Domokos (Rudolf) GPLv2

import numpy as np
import math
from fluids import ATMOSPHERE_1976 as atmosphere
import matplotlib.pyplot as pyplot
import copy
import sys

if '-p' in sys.argv:
    PLOT = True
else:
    PLOT = False


def inputParser(path):
    with open(path) as raw:
        lines = [line.split(' ') for line in raw.readlines()]
        for n in range(len(lines)):
            if '\n' in lines[n]:
                lines[n].remove('\n')
            while '' in lines[n]:
                lines[n].remove('')
    aoa = [float(n) for n in lines[0]]
    mach = []
    table = []
    for m in range(1, len(lines)):
        mach.append(float(lines[m][0]))
        table.append([float(n) for n in lines[m][1:]])
    return aoa, mach, table


def getLowHigh(table: list, point: float):
    low = None
    high = None
    for n in range(len(table)):
        if point == table[n]:
            return (table[n], table[n])
        if point > table[n]:
            low = table[n]
            try:
                high = table[n + 1]
            except IndexError:
                high = low
    return (low, high)


class table:
    def __init__(self, data):
        self.aoa = data[0]
        self.mach = data[1]
        self.table = data[2]

    def getValue(self, aoa: float, mach: float):
        """Return the interpolated table value for input point"""
        machRange = getLowHigh(self.mach, mach)
        machLow = np.interp(aoa, self.aoa,
                            self.table[self.mach.index(machRange[0])])
        machHigh = np.interp(aoa, self.aoa,
                             self.table[self.mach.index(machRange[1])])
        return np.interp(mach, machRange, [machLow, machHigh])

    def findAoA(self, mach, coeff):
        low = self.aoa[0]
        high = self.aoa[-1]
        while True:
            aoa = (high + low) / 2
            c = self.getValue(aoa, mach)
            error = abs(coeff - c)
            if error < tolerance:
                break
            elif coeff < c:
                high = aoa
            elif coeff > c:
                low = aoa
        return aoa

    def findLift(self, mach, lift, thrust):
        q = 0.5 * gamma * atmosphere(alt).P * (mach ** 2)
        low = self.aoa[0]
        high = self.aoa[-1]
        while True:
            aoa = (high + low) / 2
            thrust_lift = (thrust * math.cos(math.radians(orient_yaw))
                           * math.sin(math.radians(aoa + orient_pitch)))
            coeff = (m * g - thrust_lift) / (q * A)
            c = self.getValue(aoa, mach)
            error = abs(coeff - c)
            if error < tolerance:
                break
            elif coeff < c:
                high = aoa
            elif coeff > c:
                low = aoa
        return aoa


def neededAoA(mach, alt):
    q = 0.5 * gamma * atmosphere(alt).P * (mach ** 2)
    cl = (m * g) / (q * A)
    return CL.findAoA(mach, cl)


def getDrag(aoa, mach, alt):
    q = 0.5 * gamma * atmosphere(alt).P * (mach ** 2)
    return q * A * CDtot.getValue(aoa, mach)


# see the referenced files for an example.
# CL and CDtot are AoA v Mach, engine is alt v Mach
CL = table(inputParser('CL.txt'))
CDtot = table(inputParser('CDtot.txt'))
enginethrust = table(inputParser('./engine.txt'))
orient_yaw = 6  # positive is outwards
orient_pitch = 12  # downwards is positive
m = 19050  # ~42000 lb
A = 49.136
g = 9.8
gamma = 1.4  # ratio of specific heat
tolerance = 0.0001
v_tolerance = 0.001
milthrust = 38700
bleed = 0.03
enginecount = 2
vne = 0.9
f = 30  # Hz
dt = 1 / f
t = 0

# mil acceleration data from NAVAIR 01-85ADF-1
# {alt[m]: {speed [mach]: time[s]}}
milaccel = {0: [[0.3, 0], [0.4, 12], [0.5, 25], [0.6, 37], [0.7, 53],
                [0.75, 70], [0.8, 86], [0.825, 99], [0.844, 141]],
            10000: [[0.35, 0], [0.4, 9], [0.5, 24], [0.6, 43], [0.7, 63],
                    [0.75, 75], [0.8, 84], [0.85, 114], [0.862, 132]]
            }


error_table = copy.deepcopy(milaccel)
for alt in error_table.keys():
    for n in range(len(error_table[alt])):
        error_table[alt][n][1] = -1
for alt in milaccel.keys():
    local_mach = atmosphere(alt * 0.3048).v_sonic
    v = milaccel[alt][0][0]
    t = 0
    dv = 9999
    step = 0
    tp = []
    vp = []
    ap = []
    fp = []
    dp = []
    while dv > 0.000001:
        t += dt
        thrust = (enginethrust.getValue(alt, v) * milthrust *
                  (1 - bleed) * enginecount)
        aoa = CL.findLift(v, alt, thrust)
        thrust_eff = (thrust * math.cos(math.radians(orient_yaw))
                      * math.cos(math.radians(aoa + orient_pitch)))
        drag = getDrag(aoa, v, alt)
        a = (thrust_eff - drag) / m
        dv = a * dt / local_mach
        v += dv
        vp.append(v)
        tp.append(t)
        ap.append(a)
        fp.append(enginethrust.getValue(alt, v))
        dp.append(CDtot.getValue(aoa, v))
        error = abs(v - milaccel[alt][step][0])
        if error < v_tolerance and step < len(milaccel[alt]):
            t_error = t - milaccel[alt][step][1]
            error_table[alt][step][1] = round(t_error, 3)
            if step + 1 < len(milaccel[alt]):
                step += 1
    ts = []
    vs = []
    for n in milaccel[alt]:
        vs.append(n[0])
        ts.append(n[1])
    if PLOT:
        pyplot.plot(tp, vp, label=str(alt) + ' Mach number')
        # pyplot.plot(tp, ap, label=str(alt) + ' acceleration')
        # pyplot.plot(tp, fp, label=str(alt) + ' Thrust')
        # pyplot.plot(tp, dp, label=str(alt) + ' Drag')
        pyplot.plot(ts, vs, label=str(alt) + ' chart time')
    print(alt, error_table[alt])


if PLOT:
    pyplot.legend()
    pyplot.grid(color='b', linestyle='--', linewidth=0.5)
    pyplot.show()
