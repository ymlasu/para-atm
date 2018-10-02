# NASA NAS ULI InfoFusion



## Getting Started

Information fusion for real-time national air transportation system prognostics under uncertainty. This project highlights integration of two main software systems, PARA-ATM (Arizona State University), and NATS (Optimal Synthesis Inc).

## Installation
```
The system can be installed and run on Ubuntu Linux (VirtualBox: https://www.lifewire.com/run-ubuntu-within-windows-virtualbox-2202098). The steps are as follows:

   a.	Install java with terminal command "sudo apt-get install default-jdk" and Download Anaconda for Python version 3.5 (https://repo.continuum.io/archive/Anaconda3-2.4.0-Linux-x86_64.sh).
   b.	Save and Run “./dependencies.sh” by changing permission ("sudo chmod 777 dependencies.sh"), after changing directory to where it is located, which will install the downloaded Anaconda, with necessary Python and Postgres packages. dependencies.sh and the Downloaded Anaconda should be in the same directory.
   c.   Install NATS, as shown in the installation guide. (src/NATS/GettingStartedWith-NATS.pdf)
   d. Create database “paraatm”, with user “paraatm_user” and password ”paraatm_user” using the installed Pgadmin.
         - $ sudo -u postgres createuser paraatm_user
         - $ sudo -u postgres createdb paraatm
         - sudo -u postgres psql 
         - psql=# alter user paraatm_user with encrypted password 'paraatm_user';   
         - psql=# grant all privileges on database paraatm to paraatm_user ;
      Also, Create new server with host as 'localhost' by clicking the top left "plug" icon in PgAdmin.
   e.	Import the database backup “PARA_ATM_Database” into database “paraatm” using PgAdmin. 
         - For FAA SWIM authorized users, this backup is available in the ASU Dropbox account "/PARA_ATM_Data".
         - For public usage, the database backup can be found at "data/" folder of project root.
   f.	Pull project from GitHub into any IDE (Eclipse, IntelliJ, etc.), PyDev plugin can be found in Eclipse Marketplace.
   g. Set 'src' folder as source, by right clicking the src folder -> and selecting "Set at source folder" (According to the IDE) and change the NATS/Server/run.sh permissions by executing "sudo chmod 777 run.sh".
   h.	Run “LaunchApp.py” under package "src/PARA_ATM/Application".
   i. As of now, the flight range for FlightRadar24 data is from 03-01-2018 to 03-31-2018.
   
The video tutorial can be found at https://www.youtube.com/watch?v=8NvmqVRbXP8
```
## Application

On running LaunchApp.py, the following window would pop up:

![PARA-ATM Launch](https://image.ibb.co/cuAPWn/Screenshot_from_2018_04_19_04_45_11.png)

Action Bar:

![PARA-ATM Launch](https://image.ibb.co/c0G9xS/Screenshot_from_2018_04_19_04_45_31.png)
 
The Action Bar provides an interface to the features and operations that can be performed as part of PARA-ATM. Their functionality are as follows:
Flight: This is a drop-down list wherein all the flight from the database are listed. The flight whose trajectories need to be visualized can be selected.
From and To Date Selectors: The range of date over which the flight’s data needs to be projected can be put in here as DD/MM/YYYY.
Plot Trajectory: Hit this to view trajectory data visualized on the map.

Execute Command: The command can be put in the space provided above this button. After entering the command, hit this button to view results. Here are few of the inbuilt commands.
-	Airport(PHX): Here, the command Airport() takes the IATA Airport code as the parameter, and plots the airport ground view with live flights.
-	PlotGraph(GTI3061): This command plots the altitude vs. speed graph for the flight callsign provided as the parameters. 
-	RegressionCurve(GTI3061): This command plots the altitude vs. speed regression curve for the flight callsign provided as the parameter.
-	NATS_TrajectorySample(): This command demonstrates integration with NATS, and displays output received.

Like these, users can program custom commands, which has the following template:

### Command Functional Logic, should output an image overlay

![PARA-ATM Commands1](https://image.ibb.co/dsJRP7/commandexample.png)

### Map image overlay template

![PARA-ATM Commands2](https://image.ibb.co/n1af47/Screenshot_from_2018_04_19_03_48_53.png)

Apply Filters: Aiming to have an all-inclusive platform for data projection and analysis, there are multiple filters that can be toggled based on requirement.
-	Weather Filter: This filter when activated, adds the weather overlay over the map.
-	Airports Filter: The Airports filter marks airports across the US with details about the same.
-	Waypoints: The waypoints filter marks waypoints between the source and destination along the plotted trajectory.
-	Sectors: This filter charts out the different flying sectors that are part of the US airspace.

Run Query: 
This feature allows PARA-ATM to provide an interface to ask questions in natural language about a flight, NTSB Crash data, or related data to get output out of a semantic network, or an ontology. The query can be put into the space given space and hit “Run Query” to execute it. Here’s an example of how it works, though there is a lot more work yet to be done from the query parsing standpoint.

Live Flights:
While working with flight data, it’s always great to have a visualization of how the airspace looks that very instance. PARA-ATM has this feature embedded into it, wherein flight data is pulled in from OpenSky API. Flights are plotted like how they are with FlightRadar24, with flight details popping up by clicking on the aircraft markers.

Documentation and Help:
Hit this button to open the codebase on GitHub, which also includes this documentation. PARA-ATM is an open-source research project, and we are committed to improving it which would provide maximum learning utility. It is highly encouraged that users report bugs and raise issues on GitHub so that it can be fixed at the earliest. To get in touch with questions or suggestions, please reach out to the team.

## Contributors
```
The project has been developed under the guidance of ULI PI Dr. Yongming Liu, with student contributors 
as follows:

Hari Iyer,
PARA-ATM Founder & (Former)Lead Software Engineer,
hari.iyer@asu.edu.

Yutian Pang,
PARA-ATM Research Associate,
yutian.pang@asu.edu.
```
