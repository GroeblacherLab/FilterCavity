setup as in scheme_setup.jpg

usage of the scripts:

	- run the wlm_server_2_3 on the machine with the wavemeter (driver HighFinesse_WS6) and the optical switch (driver Sercalo_1xN_switch)
	- run the laser_lock_5_0 on the machine connected to the laser (driver TopticaDLCPro, ppcl550driver, Tl6800control) (best if via a .bat file to access remotely the correct laser server)
	- use a code like the remote_control_laser to remotely control the laser lock (or use the GUI)

All scripts can be run on the same machine