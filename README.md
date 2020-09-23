### Python toolset to create JSBSim flight dynamics models with VSPAERO
## Author: Jüttner Domokos
## Licence: GPLv2

# plotdraw.py
Generate a plot of the VSP .history output
usage:
`$ python3 plotdraw.py path/to/vsp.history parameter`

parameter may be `Mach`, `AoA`, `beta`, `CL`, `CDo`, `CDi`, `CDtot`, `CS`,
`L/D`, `E`, `CFx`, `CFz`, `CFy`, `CMx`, `CMz`, `CMy`, `T/QS`
defaults to CL

# runvsp.py
options:

	-jn
		n is the number of threads passed to vspaero with the -omp setting

	-wn
		n is the number of wake iterations, defaults to 3
		
	-d
		dryrun, all files are generated but vspaero isn't executed
		
	-c
		cleanup, removes files that are later not used. Can save large amounts
		of storage, .adb files in particular can make up ~90% of the used
		space
		
	-v
		verbose, also writes out .vsp3 for every case
		
generates .cvs, vspaero files and runs vspaero based on the parameters defined
in `runparams.json` - see included example.

requres vsp python API, see [this
page](https://kontor.ca/post/how-to-compile-openvsp-python-api/) on how to create a venv with VSP api.
run.sh and runstab.sh need to be copied into the working directory for this
script to work.

# vsp2jsbsim.py
options:

	-wn
		n is number of wake iterations, defaults to 3
		
	--debug
		enables a few extra print statements, nothing that particularly
		benefits the user, used for development
		
extracts the data from the .history files and formats them into jsbsim tables.
Takes the same runparams.json as input

It does not create the <axis> definitions, those need to be done manually

# First time setup:
- create .vsp3 model with all necessary control surfaces. control surface names should match the names in runparams['files'], except the ones specified in manual_set to be rotated instead of using subsurfaces.
- set up folder structure and create initial .vspaero files (TODO: automate this part step based on runparams.json input)
- write runparams.json

After this, each time a new version is made of the .vsp3 file, the new tables may be calculated with runvsp.py, then the data extracted with vsp2jsbsim.py.
