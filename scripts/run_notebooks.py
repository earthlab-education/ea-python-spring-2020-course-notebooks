"""
This script will convert jupyter notebooks into Jekyll-style markdown
files, and place them in the appropriate folder. It will also move
the images properly so that they are in their own separate directory.
It will only do this for notebook files that are NEWER than their
corresponding jekyll markdown files.

How to use

from the root of earth-analytics-python run

 python scripts/run_notebooks.py in-class-demos/*

# This is failing now so let's come back to the dir parameter later.
the code will figure out if it's a workshop or course and build accordingly
python scripts/run_notebooks.py dir dir-name-here

the dir name is the course or workshop directory that you wish to build.
This approach is very clunky now because it requires you to remember how to spell each directory.
in the future a dictionary would be ideal if i can figure out how to implement this.
"""
import nbformat as nf
import os
import os.path as op
import shutil as sh
import sys
import papermill as pm
import traceback
import signal

def generate_paths(notebook_path):

    """
    Generates all paths required to build an individual notebook.

    Parameters
    ----------
        notebook : str
            A string containing the path of the target notebook
            to rebuild.

    Return
    ------
        A dict that includes the website root, build path, image
        path, path for intermediate (tmp) files, and the path
        to the output .md post.

    """

    # Path to root of site - migh tnot need this
    path_root = op.abspath('')
    # Normalize path
    notebook_path = op.normpath(notebook_path)

    ## paths for pre-processing
    # Temporary directory for notebook files
    if not op.isdir(op.join('.', 'tmp')):
        os.makedirs(op.join('.', 'tmp'))

    # This is the path where the temp notebook will be stored
    path_ipynb_tmp_file = op.join('tmp', op.basename(notebook_path))

    # Create final dict of all path names
    paths = {'path_save_tmp_file': path_ipynb_tmp_file}

    return paths

def normalize_kernel_name(nb, notebook):

    """
    Updates the notebook metadata to ensure the kernel type
    is consistent with the kernel type of the conda environment.
    Outputs an updated .ipynb file written to the path of the
    target notebook.

    Parameters
    ----------
        nb: A notebook instance as read in by nbformat.
        notebook: A string containing the path of the target notebook
            to rebuild.

    Return
    ------
    None
    """

    # normalize kernel name
    kernelspec = nb.metadata.kernelspec

    if "[conda env:" in kernelspec.display_name:
        if kernelspec.language == 'python':
            if nb.metadata.language_info.version.startswith('3.'):
                kernelspec.name = 'python3'
                kernelspec.display_name = 'Python 3'
            else:
                kernelspec.name = 'python2'
                kernelspec.display_name = 'Python 2'

    nf.write(nb, notebook)


def rebuild_notebook(notebook_path):

    """
    Runs an ipynb file using papermill.
    Also handles normalizing the kernel to ensure it builds

    Parameters
    ----------

    Return
    ------
        None
    """

    # Generate paths needed to create lesson markdown and images
    paths = generate_paths(notebook_path)
    ntbk_tmp_path = paths['path_save_tmp_file']

    # Open notebook
    ntbk_json = nf.read(notebook_path, nf.NO_CONVERT)

    # --- Update notebook metadata ---
    # Normalize kernel and write to tmp dir
    normalize_kernel_name(ntbk_json, ntbk_tmp_path)

    # --- Papermill run notebook---
    print("Running notebook using papermill: ", ntbk_tmp_path)
    # Run notebook with papermill
    pm.execute_notebook(
        ntbk_tmp_path,
        ntbk_tmp_path
    )


# --- Get notebooks to rebuild - ONLY run if there are files provided to run---
if len(sys.argv) > 1:

        # otherwise, just rebuild the notebooks that were changed but REMOVE any in the ignored category
        notebooks_to_rebuild = sys.argv[1:]

        notebooks_to_rebuild = sorted(notebooks_to_rebuild)

        # Print friendly message about what is building
        if len(notebooks_to_rebuild) > 0:
            print('Processing the following dirs:')
            print('\n'.join(notebooks_to_rebuild))
        else:
            print("No changes found. There are no notebooks to rebuild.")

else:
    # exit early if no notebooks given
    sys.exit('No notebooks to rebuild.')

# --- Setup handler for rebuild timeout ---
# This is when a notebook runs very slowly like the twitter api notebooks
# might trigger this

def handler(signum, frame):
    raise Exception('Notebook build timed out.')

# Register the signal function handler
signal.signal(signal.SIGALRM, handler)

# set timeout
signal.alarm(570)

# --- Run, cleanup and convert notebooks to markdown ---

problem_notebooks = []

# Run all notebooks and create markdown
failed_count = 0
total_notebooks_built = 0
for total_num, notebook in enumerate(notebooks_to_rebuild):

    print("Building Lesson: ", notebook)

    try:
        rebuild_notebook(notebook)
        print("SUCCESS! I built:", notebook)
        total_notebooks_built += 1
    except Exception as ex:
        traceback.print_exception(type(ex), ex, ex.__traceback__)
        problem_notebooks.append(notebook)
        failed_count += 1
        continue

print("I built, ", total_notebooks_built, "notebooks.")
if failed_count > 0:
    print("Unfortunately for you, ", failed_count, "notebooks failed." )

# If the tmp dir exists clean it out
tmp_path = op.join('.', 'tmp')
if os.path.exists(tmp_path):
    sh.rmtree(tmp_path)

if len(problem_notebooks) > 0:
    # readout of notebook conversion errors
    print('\nEncountered errors with the following notebooks:\n')

    for prob in problem_notebooks:
        print(prob)
else:
    print("All notebooks built successfully!")

# write problem notebooks to log file
with open('nb_errors.txt', 'a') as log:
    for nb in problem_notebooks:
        if not nb is None: # skip writing to log if no problem notebooks
            log.write('{}\n'.format(nb))

# write successful notebooks to log file
successful_notebooks = [x for x in notebooks_to_rebuild if x not in problem_notebooks]

with open('ipynb_files_built.txt', 'w') as log:
    for nb in successful_notebooks:
        if not nb is None: # skip writing to log if no successful notebooks
            log.write('{}\n'.format(nb))
