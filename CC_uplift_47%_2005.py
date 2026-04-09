#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 18:46:45 2026

@author: Louise
"""

# Imports
import matplotlib.pyplot as plt
import pandas as pd
import bisect
import numpy as np
from array import *

# -------------------------
# Definitions/functions used
# -------------------------
def scale(x):
    x = np.asarray(x, dtype=float)
    return (x - np.nanmin(x)) / (np.nanmax(x) - np.nanmin(x))

def unscaletime(x):
    return (((np.nanmax(time) - np.nanmin(time)) * x) + np.nanmin(time))

def Q(x):  # Discharge Q given the water level h = x iff rating curve is given
    z = 0
    while z < w[-1]:
        if x > lower_limits[z] and x <= upper_limits[z]:
            y = (c[z] * ((x - a[z]) ** b[z]))
            break
        elif x > upper_limits[z]:
            z = z + 1
    else:
        y = (c[w[-1]] * ((x - a[w[-1]]) ** b[w[-1]]))
    return y

# -------------------------
# User settings
# -------------------------
ncheck = 1  # Superfluous test/check figures ; set ncheck=0 to remove
(nriver, nratingc, nriverflag) = (1, 0, 0)

if nriver == 1:
    Data = pd.read_csv('River_Eden_Sheepmount_All_Measures_6-10_Dec_2005.csv')
    ht = 7.2          # Threshold (set to what you want, e.g. 4.95)
    error = 0.035     # overall error
    stitle = 'River Eden at Sheepmount 2005 Climate uplift 47%'

# -------------------------
# Force numeric + build separate clean baseline and CC datasets
# -------------------------
for col in ['Time', 'Height', 'Flow', 'Time CC47', 'Height CC47', 'Flow CC47']:
    if col in Data.columns:
        Data[col] = pd.to_numeric(Data[col], errors='coerce')

Base = Data.dropna(subset=['Time', 'Height', 'Flow']).reset_index(drop=True)
CC   = Data.dropna(subset=['Time CC47', 'Height CC47', 'Flow CC47']).reset_index(drop=True)

# Climate uplift arrays (these drive FEV/box/fill)
time   = CC['Time CC47'].to_numpy(dtype=float)
height = CC['Height CC47'].to_numpy(dtype=float)
Flow   = CC['Flow CC47'].to_numpy(dtype=float)

# Baseline/original arrays (for red dashed overlays only)
time0   = Base['Time'].to_numpy(dtype=float)
height0 = Base['Height'].to_numpy(dtype=float)
Flow0   = Base['Flow'].to_numpy(dtype=float)

# -------------------------
# Establish flow/discharge data either from "Data" file or via rating curve
# -------------------------
if nratingc == 1:
    w = []
    for i in range(len(a)):
        w.append(i)

    qt = Q(ht)
    qtmin = (1.0 - error) * qt
    qtmax = (1.0 + error) * qt

    Flow = []
    Flowmin = []
    Flowmax = []
    for i in height:
        Flow.append(Q(i))
        Flowmin.append((1.0 - error) * Q(i))
        Flowmax.append((1.0 + error) * Q(i))

    scaledFlow = []
    for i in Flow:
        scaledFlow.append((i - min(Flow)) / (max(Flow) - min(Flow)))

elif nratingc == 0:
    # IMPORTANT: DO NOT overwrite Flow with baseline.
    # Flow is already set to CC['Flow CC'] above.
    nend = len(time)

    if nriverflag > 0:  # slice arrays (CC arrays)
        lent = len(time)
        time1 = np.zeros(lent - nriverflag)
        height1 = np.zeros(lent - nriverflag)
        Flow1 = np.zeros(lent - nriverflag)
        time1[0:lent - nriverflag] = time[nriverflag:lent]
        height1[0:lent - nriverflag] = height[nriverflag:lent]
        Flow1[0:lent - nriverflag] = Flow[nriverflag:lent]
        del time, height, Flow
        (time, height, Flow) = (time1, height1, Flow1)
        del time1, height1, Flow1
        print('hallo WARNING: very clumsy way of slicing and reducing; please improve')

    print('nend, nendnew', nend, len(time))

    scaledFlow = []
    for i in Flow:
        scaledFlow.append((i - min(Flow)) / (max(Flow) - min(Flow)))

    Flowmin = (1.0 - error) * Flow
    Flowmax = (1.0 + error) * Flow

    # Find qt, qtmin, qtmax from CC height/flow
    nwin = 0
    for i in range(1, len(height)):
        if height[i] > ht and height[i - 1] < ht and nwin == 0:
            qt = Flow[i - 1] + (Flow[i] - Flow[i - 1]) * (ht - height[i - 1]) / (height[i] - height[i - 1])
            nwin = 1
        if height[i] < ht and height[i - 1] > ht and nwin == 0:
            qt = Flow[i - 1] + (Flow[i] - Flow[i - 1]) * (ht - height[i - 1]) / (height[i] - height[i - 1])
            nwin = 1

    qtmin = (1.0 - error) * qt
    qtmax = (1.0 + error) * qt

    if ncheck == 1:
        plt.figure(101)
        plt.plot(height, Flow, '-')
        plt.xlabel('$h$ (m)', fontsize=16)
        plt.ylabel('$Q(h)$ (m$^3$/s)', fontsize=16)

        plt.figure(102)
        plt.plot(time, Flow, '-')
        plt.xlabel('$t$ (days)', fontsize=16)
        plt.ylabel('$Q(t)$ (m$^3$/s)', fontsize=16)

# -------------------------
# Scalings (CC)
# -------------------------
time_increment = (time[1] - time[0]) * 24 * 3600
number_of_days = int((len(time) * (time[1] - time[0])))

scaledtime = scale(time)
scaledheight = scale(height)

scaledFlow_up = [i * (1 + error) for i in scaledFlow]
scaledFlow_down = [i * (1 - error) for i in scaledFlow]

negheight = -scaledheight
negday = -(scaledtime)

# -------------------------
# Baseline overlays scaled onto CC ranges + CLIPPED to [0,1] (Option A)
# -------------------------
scaledtime0   = (time0   - np.nanmin(time))   / (np.nanmax(time)   - np.nanmin(time))
scaledheight0 = (height0 - np.nanmin(height)) / (np.nanmax(height) - np.nanmin(height))
scaledFlow0   = (Flow0   - np.nanmin(Flow))   / (np.nanmax(Flow)   - np.nanmin(Flow))

# Clip so red dashed never goes outside axes box
scaledtime0   = np.clip(scaledtime0,   0.0, 1.0)
scaledheight0 = np.clip(scaledheight0, 0.0, 1.0)
scaledFlow0   = np.clip(scaledFlow0,   0.0, 1.0)

negheight0 = -scaledheight0
negday0 = -scaledtime0

# -------------------------
# Figures
# -------------------------
plt.rcParams["figure.figsize"] = [12, 12]
plt.rcParams['axes.edgecolor'] = 'white'

fig, ax = plt.subplots()
ax.spines['left'].set_position(('zero'))
ax.spines['bottom'].set_position(('zero'))
ax.spines['left'].set_color('black')
ax.spines['bottom'].set_color('black')

# CC (black)
ax.plot(negheight, scaledFlow, 'black', linewidth=1)
ax.plot([0, -1], [0, 1], 'blue', linestyle='--', marker='', linewidth=2)
ax.plot(scaledtime, scaledFlow, 'black', linewidth=1)
ax.plot(negheight, negday, 'black', linewidth=1)

# Baseline (red dashed overlays)
ax.plot(negheight0, scaledFlow0, 'r--', linewidth=1.5)      # upper-left
ax.plot(scaledtime0, scaledFlow0, 'r--', linewidth=1.5)      # hydrograph
ax.plot(negheight0, negday0, 'r--', linewidth=1.5)           # lower-left

# -------------------------
# Threshold scalings (CC)
# -------------------------
scaledht = (ht - min(height)) / (max(height) - min(height))
scaledqt = (qt - min(Flow)) / (max(Flow) - min(Flow))

QT = []
for _ in scaledFlow:
    QT.append(scaledqt)

SF = np.array(scaledFlow)
e = np.array(QT)

# FEV fill (CC)
ax.fill_between(scaledtime, SF, e, where=SF >= e, facecolor='blue', alpha=0.4)
idx = np.argwhere(np.diff(np.sign(SF - e))).flatten()

f = scaledtime[idx[0]]
g = scaledtime[idx[-1]]

C = unscaletime(f)
d = unscaletime(g)

Tf = (d - C) * 24  # hours

time_increment = (time[1] - time[0]) * 24 * 3600

flow = []
for i in Flow:
    if i >= qt:
        flow.append((i - qt) * (time_increment))
flowmin = []
for i in Flowmin:
    if i >= qtmin:
        flowmin.append((i - qtmin) * (time_increment))
flowmax = []
for i in Flowmax:
    if i >= qtmax:
        flowmax.append((i - qtmax) * (time_increment))

FEV = sum(flow)
FEV_min = sum(flowmin)
FEV_max = sum(flowmax)

Tfs = Tf * (60 ** 2)
qm = (FEV / Tfs) + qt
scaledqm = (qm - min(Flow)) / (max(Flow) - min(Flow))

hm = ht  # WARNING Poor fix for nriver=3
if nratingc == 1:
    hm = ((qm / c[-1]) ** (1 / b[-1])) + a[-1]
elif nratingc == 0:
    nwin = 0
    for i in range(1, len(Flow)):
        if Flow[i] > qm and Flow[i - 1] < qm and nwin == 0:
            hm = height[i - 1] + (height[i] - height[i - 1]) * (qm - Flow[i - 1]) / (Flow[i] - Flow[i - 1])
            nwin = 1
        if Flow[i] < qm and Flow[i - 1] > qm and nwin == 0:
            hm = height[i - 1] + (height[i] - height[i - 1]) * (qm - Flow[i - 1]) / (Flow[i] - Flow[i - 1])
            nwin = 1

scaledhm = (hm - min(height)) / (max(height) - min(height))

# Lines and box (CC)
ax.plot([-scaledht, -scaledht], [-1, scaledqt], 'black', linestyle='--', linewidth=1)
ax.plot([-scaledhm, -scaledhm], [-1, scaledqm], 'black', linestyle='--', linewidth=1)
ax.plot([-scaledht, 1], [scaledqt, scaledqt], 'black', linestyle='--', linewidth=1)
ax.plot([-scaledhm, 1], [scaledqm, scaledqm], 'black', linestyle='--', linewidth=1)

ax.plot([f, f, f], [scaledqt, scaledqm, -1/5], 'black', linestyle='--', linewidth=1)
ax.plot([g, g, g], [scaledqt, scaledqm, -1/5], 'black', linestyle='--', linewidth=1)
ax.plot([f, f], [scaledqm, scaledqt], 'black', linewidth=1.5)
ax.plot([f, g], [scaledqm, scaledqm], 'black', linewidth=1.5)
ax.plot([f, g], [scaledqt, scaledqt], 'black', linewidth=1.5)
ax.plot([g, g], [scaledqm, scaledqt], 'black', linewidth=1.5)

# -------------------------
# Axis ticks (CC-based)
# -------------------------
h = []
for i in np.arange(1, number_of_days + 1):
    h.append(i / number_of_days)

# >>> CHANGED: discharge tick increment now 100 instead of 50 <<<
flow_tick = 100
l = np.arange(0, max(Flow) + flow_tick, flow_tick)
m = bisect.bisect(l, min(Flow))

n = []
for i in np.arange(l[m], max(Flow) + flow_tick, flow_tick):
    n.append(int(i))

# Height ticks unchanged (still every 1 m)
o = np.arange(0, max(height) + 1, 1)
p = bisect.bisect(o, min(height))

q = []
for i in np.arange(o[p], max(height) + 1, 1):
    q.append(i)

k = []
for i in q:
    k.append(-(i - min(height)) / (max(height) - min(height)))

j = []
for i in n:
    j.append((i - min(Flow)) / (max(Flow) - min(Flow)))

ticks_x = k + h

r = []
for i in h:
    r.append(-i)

ticks_y = r + j

s = []
for i in np.arange(1, number_of_days + 1):
    s.append(i)

Ticks_x = q + s
Ticks_y = s + n

ax.set_xticks(ticks_x)
ax.set_yticks(ticks_y)
ax.set_xticklabels(Ticks_x)
ax.set_yticklabels(Ticks_y)

# Uncertainty shading (CC)
lists1 = sorted(zip(*[negheight, scaledFlow_down]))
negheight1, scaledFlow_down1 = list(zip(*lists1))

lists2 = sorted(zip(*[negheight, scaledFlow_up]))
negheight1, scaledFlow_up1 = list(zip(*lists2))

ax.fill_between(negheight1, scaledFlow_down1, scaledFlow_up1, color="grey", alpha=0.3)
ax.fill_between(scaledtime, scaledFlow_up, scaledFlow_down, color="grey", alpha=0.3)
QtU = scaledqt * (1 + error)
QtD = scaledqt * (1 - error)
ax.fill_between([scaledtime[idx[0]], scaledtime[idx[-1]]], QtU, QtD, color="grey", alpha=0.3)

ax.tick_params(axis='x', colors='black', direction='out', length=9, width=1)
ax.tick_params(axis='y', colors='black', direction='out', length=9, width=1)

plt.text(-scaledht + 0.02, -1, '$h_T$', size=15)
plt.text(-scaledhm + 0.02, -1, '$h_m$', size=15)
plt.text(1, scaledqm, '$Q_m$', size=15)
plt.text(1, scaledqt, '$Q_T$', size=15)
plt.text(((f + g) / 2) - 1/50, -0.18, '$T_f$', size=15)
plt.text(0.02, 1.05, 'Q $[m^3/s]$', size=15)
plt.text(0.95, -0.2, 't [day]', size=15)
plt.text(-0.18, -1.11, 't [day]', size=15)
plt.text(-1.1, 0.02, '$\\overline {h}$ [m]', size=15)
plt.title(f"{stitle}")

ax.scatter(0, 0, color='white')

A = round(FEV / (10 ** 6), 2)
B = round(Tf, 2)
C_ = round(ht, 2)
D_ = round(hm, 2)
E_ = round(qt, 2)
F_ = round(qm, 2)
Amax = round(FEV_max / (10 ** 6), 2)
Amin = round(FEV_min / (10 ** 6), 2)
Emin = round(qtmin, 2)
Emax = round(qtmax, 2)

plt.text(0.4, -0.325, '$FEV$ ≈ ' + str(A) + 'Mm$^3$', size=15)
plt.text(0.4, -0.4, '$T_f$ = ' + str(B) + 'hrs', size=15)
plt.text(0.4, -0.475, '$h_T$ = ' + str(C_) + 'm', size=15)
plt.text(0.4, -0.55, '$h_m$ = ' + str(D_) + 'm', size=15)
plt.text(0.4, -0.625, '$Q_T$ = ' + str(E_) + 'm$^3$/s', size=15)
plt.text(0.4, -0.7, '$Q_m$ = ' + str(F_) + 'm$^3$/s', size=15)
plt.text(0.4, -0.775, '$FEV_{max}$ ≈ ' + str(Amax) + 'Mm$^3$', size=15)
plt.text(0.4, -0.85, '$FEV_{min}$ ≈ ' + str(Amin) + 'Mm$^3$', size=15)
plt.text(0.4, -0.925, '$Q_{Tmax}$ = ' + str(Emax) + 'm$^3$/s', size=15)
plt.text(0.4, -1.0, '$Q_{Tmin}$ = ' + str(Emin) + 'm$^3$/s', size=15)

plt.savefig("test.png")
plt.show(block=True)
plt.pause(0.001)
plt.gcf().clear()
plt.show(block=False)

print("Finished program!")

# -------------------------
# Square Lake Plot Code
# -------------------------
fig = plt.figure(figsize=plt.figaspect(1) * 0.7)
ax = fig.add_subplot(projection='3d')
plt.rcParams['axes.edgecolor'] = 'white'
plt.rcParams["figure.figsize"] = [10, 8]

ax.grid(False)
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False

ax.xaxis.pane.set_edgecolor('w')
ax.yaxis.pane.set_edgecolor('w')
ax.zaxis.pane.set_edgecolor('w')

depth = hm - ht
sl = (FEV / depth) ** 0.5

a = [sl, sl]
b = [sl, sl]
c_ = [depth, 0]

d = [sl, 0]
e_ = [sl, sl]
f_ = [0, 0]

g_ = [sl, sl]
h_ = [sl, 0]
i_ = [0, 0]

ax.plot(a, b, c_, '--', color='k')
ax.plot(d, e_, f_, '--', color='k')
ax.plot(g_, h_, i_, '--', color='k')

x = [sl, sl, sl, 0, 0, 0, sl, sl, 0, 0, 0, 0]
y = [sl, 0, 0, 0, 0, sl, sl, 0, 0, 0, sl, sl]
z = [depth, depth, 0, 0, depth, depth, depth, depth, depth, 0, 0, depth]

ax.plot(x, y, z, color='k')

ax.text(5 * (sl / 9), -4 * (sl / 9), 0, 'Side-Length [m]', size=11)
ax.text(-sl / 6, sl / 10, 0, 'Side-Length [m]', size=11)
ax.text(0.15 * sl, sl, 2.8, 'Depth [m]', size=11)

ax.text(7 * (sl / 10), 6 * (sl / 4), 1, '' + str(int(round(sl))) + 'm', size=13)
ax.text(15 * (sl / 10), 9 * (sl / 10), 1, '' + str(int(round(sl))) + 'm', size=13)

ax.set_zticks([0, depth])
ax.set_xlim(sl, 0)
ax.set_ylim(0, sl)
ax.set_zlim(0, depth * 1.5)

plt.title("River Eden at Sheepmount 2005 Square Lake Plot", size=30)
plt.show()