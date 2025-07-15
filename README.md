# How to use it

## 1. First clone the git repository in your workdirectory:

```
git clone https://github.com/JuginPower/analyzer.git
```

And if you want to use the datalayer submodule, type in the terminal:

```commandline
git submodule init
git submodule update
```

Like in the technical docs for [git submodules](https://git-scm.com/book/de/v2/Git-Tools-Submodule).

## 2. Install the environment

It's important to let the global installation of python and all the standard library clean on your desktop pc.
So please make sure to have a *[virtual environment](https://www.w3schools.com/python/python_virtualenv.asp)*.
You can create your virtual environment where ever you want on disk with the necessary permissions.

And activate it!

**For Linux:**

```commandline
python -m venv analyzer-env
source analyzer-env/bin/activate 
```

I think it's only for linux users. In cases where your operating system does not have the python3-venv library 
installed, you must first install it via `sudo apt-get install python3-venv `

**For Windows:**

```commandline
C:\Users\projectdirectory> python -m venv analyzer-env
C:\Users\projectdirectory> analyzer-env\Scripts\activate 
```

After that you should see the name of your virtual environment in front of the cursor, such as 
`(analyzer-env) eugen@eugen-ubuntu:~/Schreibtisch/projects/analyzer$`.


## 3. Install packages which are depends on your usecases

Now you can install all the program libraries you need for your **purposes**.

For `frontplot.ipynb` type `... -r req-frontplot.txt` instead `... -r req.txt`

- For Linux:

```commandline
python -m pip install -r req.txt
```

- For Windows

```commandline
py -m pip install -r req.txt
```

