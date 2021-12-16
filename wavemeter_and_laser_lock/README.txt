HOW TO USE THE CODE:

	1 - build a setup as shown in scheme_setup.jpg
	2 - run the wavemeter_server.py on the machine connected to the wavemeter (driver HighFinesse_WS6 in the example) and the optical switch (driver Sercalo_1xN_switch in the example)
	3 - run the laser_lock on the machine connected to the laser (driver TopticaDLCPro in the example) 
	4 - use the GUI, or run remote_control_laser.py to remotely control the laser lock 



If used a other laser than the TopticaDLCPro you need to write a driver.
If a single laser is locked the 1xN switch is not needed and the relative part in wavemeter_server.py can be removed,

Using the HighFinesse_WS6 as wavemeter and 3 lasers locked at the same time, the feedback for each laser is every 0.6 second and a stability of +-1MHz around the desired wavelenght is achieved. 

