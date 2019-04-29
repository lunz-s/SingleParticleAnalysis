# Script that calls Relion for data generation
import subprocess as sp
import os
import fnmatch
import sys

GPU_ids = ''
NUM_MPI = 3 #  At least 3 if --split_random_halves is used

base_path = '/local/scratch/public/sl767/MRC_Data'

def runCommand(cmd_string):
    sp.call(cmd_string.split(' '))


RELION_EXTERNAL_RECONSTRUCT_EXECUTABLE = '/mhome/maths/s/sl767/PythonCode/SingleParticleAnalysis/ext_reconstruct_AR.py'
# runCommand('export RELION_EXTERNAL_RECONSTRUCT_EXECUTABLE="{}"'.format(RELION_EXTERNAL_RECONSTRUCT_EXECUTABLE))


train_path = base_path + '/org/training'

noise_level = ['02'] #  Right now this has to be a list with a single element
out_path = base_path + '/Data_0{}_10k'.format(noise_level[0])
out_new_path = base_path + '/Data_0{}_10k/TestAR'.format(noise_level[0])
#print(out_path)

PDB_ID = ['5A0M']
MPI_MODE = 'mpirun'

for p in PDB_ID:
    for n in noise_level:
        if MPI_MODE == 'mpirun':
            refine_cmd = 'mpirun -n {NUM_MPI} relion_refine_mpi'
        elif MPI_MODE == 'srun':
            refine_cmd = 'srun --mpi=pmi2 relion_refine_mpi'
        elif MPI_MODE == 'mpirun-hpc':
            refine_cmd = 'mpirun relion_refine_mpi'
        else:
            raise Exception 
        refine_cmd += ' --o {ONP}/{p}/{p}_mult0{n}'
        refine_cmd += ' --auto_refine --split_random_halves'
        refine_cmd += ' --i {OP}/projs/{p}/{p}_mult0{n}.star'
        refine_cmd += ' --ref {OP}/SGD/{p}/{p}_mult0{n}_it300_class001.mrc'# --ini_high 30'
        refine_cmd += ' --pad 1'
        refine_cmd += ' --particle_diameter 150 --flatten_solvent --zero_mask --oversampling 1'
        refine_cmd += ' --healpix_order 2 --offset_range 5'
        refine_cmd += ' --auto_local_healpix_order 4'
        refine_cmd += ' --offset_step 2 --sym C1'
        refine_cmd += ' --low_resol_join_halves 40'
        refine_cmd += ' --norm --scale'
        refine_cmd += ' --gpu "{GPU_ids}"'
        refine_cmd += ' --external_reconstruct' # --maximum_angular_sampling 1.8'
        refine_cmd += ' --j 6' # Number of threads to run in parallel (only useful on multi-core machines)
        refine_cmd += ' --pool 30' # Number of images to pool for each thread task
        refine_cmd += ' --dont_combine_weights_via_disc'  # Send the large arrays of summed weights through the MPI network,
                                                          # instead of writing large files to disc
#            refine_cmd += ' --iter 30'
#            refine_cmd += ' --preread_images' #  Use this to let the master process read all particles into memory.
                                           #  Be careful you have enough RAM for large data sets!
        refine_cmd = refine_cmd.format(OP=out_path, p=p, n=n, GPU_ids=GPU_ids, NUM_MPI=NUM_MPI, ONP=out_new_path)
        runCommand(refine_cmd) 
