# How to use it

## 1. First clone the git repository in your workdirectory:

Open your terminal and type:

```commandline
git clone https://github.com/JuginPower/analyzer.git
```

Change the directory:

```commandline
cd analyzer
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

Your pip installation is sometimes not the newest, make sure to actualize it:

**For Linux:**

```commandline
python -m pip install --upgrade pip 
```

**For Windows:**

```commandline
py -m pip install --upgrade pip
```

It's better to start with the newest package manager to avoid further problems of installing arbitrary packages in 
your virtual environment.

## 3. Install packages

Now you can install all the program libraries you need to run all scripts in this project.

- For Linux:

```commandline
python -m pip install -r req.txt
```

- For Windows

```commandline
py -m pip install -r req.txt
```

It install all necessary dependencies in [req.txt](req.txt).

## 4. Make necessary directories

For the program you need especially the *images* and the *data* folder, please make them with:

```commandline
mkdir data
mkdir images
```

## 5. Open the notebooks

To use one of the previously created notebooks, first launch jupyter notebook in the terminal. Enter:

```commandline
jupyter notebook
```

And have fun with analyzer! :smiley:

## 6. Close the program after finishing

After you closed your browser please avoid it to simply shut down your code editor or the terminal where the notebook
is started. Type `CTRL+C` to shut down the notebook kernel in the terminal and follow the instructions.
