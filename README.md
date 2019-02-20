# Reproducing open-projects software builds experiment

Research on reproducing software builds in past commits

## Introduction

We will build the projects in all the versions that repository provides to check the status of the project and analyze the cases in which it is not possible to carry out the construction. The proyects selected for this experiment are the following:

| Identifier       	| Project             	| # of commits 	|
|------------------	|---------------------	|--------------	|
| spring-framework 	| Spring Framework    	| 17382        	|
| Closure          	| Closure compiler    	| 2858         	|
| Lang             	| Apache commons-lang 	| 3570         	|
| Math             	| Apache commons-math 	| 4878         	|
| Mockito          	| Mockito             	| 2639         	|
| Time             	| Joda-Time           	| 1717         	|

## Prerequisites

- Git 2.17.1
- Conda 4.5.3
- [Defects4J 1.2.0](https://github.com/rjust/defects4j/tree/v1.2.0) (install as indicate in README.md)

# SetUp

Clone the project repo:

```
  git clone https://gitlab.com/urjc-softdev/bugs.git
```

Download repos from git and Defects4J:

```
  cd projects
  git clone https://github.com/spring-projects/spring-framework.git
  defects4j checkout -p Lang -v 1b -w Lang/
  defects4j checkout -p Math -v 1b -w Math/
  defects4j checkout -p Closure -v 1b -w Closure/
  defects4j checkout -p Mockito -v 1b -w Mockito/
  defects4j checkout -p Time -v 1b -w Time/
```

# Start the experiment

To check build history from a project:

```
python py/checkBuildHistory.py configFiles/CheckBuildHistoryFiles/<project>-step<n>-config.json
```

#### :heavy_exclamation_mark: **IMPORTANT**: The experiment for each project can take several hours or days, depending of your machine. All results to realize the analysis are provided in this repo.

For example (assuming analysis/Lang/step_1/ doesn't exist):

```
python py/checkBuildHistory.py configFiles/CheckBuildHistoryFiles/Lang-step1-config.json
```

Then, you will see the following message:

```
WRITE A BUILD SCRIPT FOR PROJECT AT analysis/Lang/step_1/build-Lang.sh
```

Write build script or copy it from `configFiles/BuildFiles/build-Lang.sh` and run the command again:

```
python py/checkBuildHistory.py configFiles/CheckBuildHistoryFiles/Lang-step1-config.json
```

This will create new folder `analysis/Lang/step_1/` with the following files/subfolders:

- `general_logs/` include the logs from the script `checkBuildHistory.py`
- `logs/` include the logs from each build/commit
- `build-Lang.sh` the script to build the project
- `report_step_1.csv` a table in csv format with the results of experiment for this project

The `report_step_1.csv` file follows this format:

```
id,commit,build,exec_time,comment,fix
0,687b2e62,SUCCESS,6,LANG-747 NumberUtils does not handle Long Hex numbers,{}
```

- `id` is the identifier, and also shows how much commits are checked from latest commit.
- `commit` hash id from the commit to identify it in Git
- `build` status of the build. Could be 'SUCCESS', 'FAIL' or 'NO' (not already checked)
- `exec_time` time in seconds that the builds take 
- `comment` git comment of the commit
- `fix` a JSON object to store any info from any future fix

# Analyce results

Once all commits was checked, we could analyce the results using a JupyterNotebook:

```
jupyter-notebook
```

Navigate to `/analysis/_notebooks/LangAnalysis.ipynb` and run notebook to see the analysis.