'''
This script reads every line of "changed_files.txt" and stores each line as an element in a list
From this list, we then parse out .ipynb files, .Rmd files, and image files (.jpg, .jpeg, .gif)
'''

with open("changed_files.txt") as f:
    content = f.readlines()
    print("HERE:", content)
content = [x.strip() for x in content]

changed_notebooks = [line for line in content if line.endswith(".ipynb")]

print("The following Jupyter Notebooks were changed in this commit. I will run each one: ", changed_notebooks)

with open("changed_notebooks.txt", "w") as f:
    if len(changed_notebooks) > 0:
        for fn in changed_notebooks:
            f.write("%s\n" % fn)
