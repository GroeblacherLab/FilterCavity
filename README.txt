Inventor files for a set of free spce Fabry-Perot cavities.


---------------- files ----------------------------------

In the 'assembly18ghz.iam' there is the mounted components. 
The components (parts) are in the separate inventor files: 
'XXghzenclosure.ipt', for the cilindrical body of the cavity with a FSR of XX GHz
'back.ipt', to close the back opening were the piezo element is placed
'holder.ipt', to connect one of the mirror to the piezo element
'HPSt 15014-102 VS22.ipt', piezo element as from https://www.piezomechanik.com/fileadmin/content_files/products/actuators/actuators-3-piezo-ring-actuators-hpst150-tubular.pdf , model HPSt150/14-10/12 VS22
'Mirror.ipt', mirror as from https://www.layertec.de/en/shop/datasheet-105081/ , 
	105081 - for cavities with FWHM of 50MHz
	Output Coupler:
	FS, pl-concave, Ø=12.7-0.1mm, te=6.35±0.1mm, //<5min,
	S1: Øe10, L/10,
	AR(0°, 1400-1700nm)<0.2%,
	S2(^): Øe10, L/4reg., r=50(±0.5%)mm,
	PR(0°,1450-1670±10nm)=99.3...99.4%

	103671 - for cavities with FWHM of 150MHz
	Output Coupler:
	FS, pl-concave, Ø=12.7-0.1mm, te=6.35±0.1mm
	S1: Øe10, L/10
	AR(0°, 750-850 + 1450-1650nm)<0.6%,
	S2(^): Øe10, L/4reg., r2=30(±0.5%)mm
	PR(0°, 1450-1650±10nm)=98±0.75% + R(0°, 750-850±8nm)<5%
'screw.ipt', to connect one of the mirror to the cavity cilindrical body
'washer.ipt', some spacers to support the mirrors


---------------- driving ----------------------------------

Driving the piezo with +- 10V gives a scan range of ~25GHz, so always visible one transmission peak.


---------------- specs ----------------------------------

Using two (2) cavities in series with FWHM of 50MHz each OR three (3) cavities in series with FWHM of 150MHz the suppression at 5GHz from the transmission peak is ~90dB.