*** Python toolset to create JSBSim flight dynamics models with VSPAERO
** Author: Jüttner Domokos
** Licence: GPLv2

* plotdraw.py
Generate a plot of the VSP .history output
usage:
`$ python3 plotdraw.py path/to/vsp.history parameter`
parameter may be `Mach`, `AoA`, `beta`, `CL`, `CDo`, `CDi`, `CDtot`, `CS`,
`L/D`, `E`, `CFx`, `CFz`, `CFy`, `CMx`, `CMz`, `CMy`, `T/QS`
defaults to CL

* runvsp.py
generates .cvs, vspaero files and runs vspaero based on the parameters defined
in `runparams.json`
requres vsp python API, see [this
page](https://kontor.ca/post/how-to-compile-openvsp-python-api/) on how to
compile create a venv with VSP api.

* vsp2jsbsim.py
extracts the data from the .history files and formats them into jsbsim tables.
Takes the same runparams.json as input
