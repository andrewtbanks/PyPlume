# -*- coding: utf-8 -*-
"""
Created on Mon May 15 15:35:53 2023

@author: sndn


to do 

method to efficiently sceen the file by only parsing header info
add position data and other metadata to csv output
"""
###############################################################################

import os
import warnings
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET


import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.collections import LineCollection
import matplotlib.ticker as mticker


import copy


from ..ptools import ptools
from ..plotting.matplotlib_shell import subplots, dhi_colors


np.seterr(divide='ignore', invalid='ignore')
###############################################################################

class seabird_ctd:
    def __init__(self, filepath_hex, filepath_xml,**kwargs):
        
        verbose = kwargs.pop('verbose',0)
        
        self._filepath_hex = filepath_hex
        self._filepath_xml = filepath_xml
        
        self.data = {}
        import_file = kwargs.pop('import_file',True)
        if not import_file:
            self.__detect_sensors()
            self.__parse_xml()
            self.__parse_hex()
        else:
            self.__detect_sensors()
            self.__parse_xml()
            self.__parse_hex()
            
            
            if verbose >0 : self.__print_metadata()   # Comment out to mute metadata
            
            self.__get_xml_coefficients()
            
            try:
                self.__get_hex_coefficients()
                self.__compare_coefficients()
            except:
                None
                #print('No hex coefficients found')
            
            
            self.__hex2temperature()
            self.__hex2pressure()
            self.__hex2conductivity()
            self.__conductivity2salinity()
            
            if 'TurbidityMeter' in self._sensors:
                self.__hex2turbidity()
                
            if 'WET_LabsCStar' in self._sensors:
                self.__hex2transmission()
                
            if 'OxygenSensor' in self._sensors:
                self.__hex2oxygen()


    def __detect_sensors(self):
        
        """
        
        Detects all instruments found in the xml configuration file (.xmlcon) and stores their names in self._sensors
        
        """
        
        self._sensors = []
        self._sensor_index = {}
        
        
        
        tree = ET.parse(self._filepath_xml)
        root = tree.getroot()

        sensors = root.findall('Instrument/SensorArray/Sensor')
        
        #get number of external voltage channels 
        if root.find('Instrument/ExternalVoltageChannels'):
            n_ext_sensors = int(root.find('Instrument/ExternalVoltageChannels').text)
        else:
            n_ext_sensors = 0
        
        sensor_idx = 0
        for sensor in sensors:
            for child in sensor:
                if child.tag != 'NotInUse':
                    
                    self._sensors.append(child.tag)
                    
                    
                    # set sensor index in order read from file
                    self._sensor_index[child.tag] = sensor_idx
                    sensor_idx +=1
                    
    def __print_metadata(self):
        
        """
        
        Prints file metadata to standard output (terminal)
        
        """
        
        print('\n#################### Seabird CTD Hex File ####################\n')
        print("\033[4m" + 'METADATA' + "\033[0m" + '\n')
        print('    ' + "\033[4m" + 'Instrument name' + "\033[0m" + f': {self._xmlcon["Name"]}')
        print('    ' + "\033[4m" + 'File name' + "\033[0m" + f': {os.path.basename(self._filepath_hex)}')
        print('    ' + "\033[4m" + 'File size' + "\033[0m" + f': {os.path.getsize(self._filepath_hex):,} bytes')
        print('    ' + "\033[4m" + 'Number samples' + "\033[0m" + f': {self.n_samples:,}')
        
        print('    ' + "\033[4m" + 'Attached sensors'+ "\033[0m" + ':')
        for sensor in self._sensors:
            print(f'        {sensor}')
        

    def __parse_xml(self):
        
        """
        
        Extracts information from the xml configuration file (.xmlcon) and stores it in self._xmlcon dictionary
        
        """
        global root,tree
        self._xmlcon = {}
        
        tree = ET.parse(self._filepath_xml)
        root = tree.getroot()
        
        self._xmlcon['Name'] = root.find('Instrument/Name').text
        
        self._xmlcon['Sampling Interval'] = float(root.find('Instrument/SampleIntervalSeconds').text)
    

    def __parse_hex(self):
        
        """
        
        Extracts information from SBE16/19 hex files such as hexadecimal strings (stored in self._hex_samples)
        and number of samples.
        
        Constructs timestamps for each sample and stores them in self.data['DateTime']
        
        """
        
        
        hex_file = open(self._filepath_hex, 'r')
        hex_data = hex_file.read()
        hex_file.close()
        
        self._hex_samples = hex_data.split('*END*')[1].strip().split('\n')
        a = self._hex_samples
        
        hex_header = hex_data.split('*END*')[0].strip().split('\n')
        

        time_start = []         # Array to store start times for each sampling period in the file 
        number_samples = []     # Array to store number of samples for each sampling period in the file
  
        
        found= False # indicator if the * hdr was found (for method 1)

        ## method 1 (works for IP instruments)
        for line in hex_header:
            if '* hdr' in line or '* cast' in line:
                found = True
                time_start.append(pd.to_datetime(line.split('samples')[0][-21:]))
                sample_range = [int(i) for i in line.split('samples')[1].split(',')[0].split('to')]
                n_samples = (sample_range[1] - sample_range[0]) + 1
                number_samples.append(n_samples)
                
                sampling_freq = 1/(int(.1*self._xmlcon['Sampling Interval']))
                #print(sampling_freq)
                timestep = pd.Timedelta(value=1/sampling_freq, unit='seconds')
                
                
                if 'int' in line:
                    timestep = int(line.split('int = ')[1].split(',')[0])
                    timestep = pd.Timedelta(timestep, unit = 'seconds')
                    
                    
                date_time = pd.date_range(start=time_start[0], periods=0, freq=timestep) # Create empty DatetimeIndex 
                for i in range(len(time_start)):
                    daterange = pd.date_range(start=time_start[i], periods=number_samples[i], freq=timestep)
                    date_time = date_time.append(daterange)
                
                self.n_samples = sum(number_samples)
                self.data['DateTime'] = date_time
                    
  
        if not found:
            #method 2 (works for HG instruments)
            #Procedure for parsing DeckSamplingSBE hex headers

            n_samples = len(self._hex_samples) 

            hex_header = hex_data.split('*END*')[0]
            time_start = pd.to_datetime(hex_header.split('* System UTC = ')[1])
            time_step = float(hex_header.split('* Real-Time Sample Interval = ')[1].split('seconds')[0])
            time_step = pd.Timedelta(value=time_step, unit='seconds')
            self.n_samples = n_samples
            self.data['DateTime'] = pd.date_range(start=time_start, periods=n_samples, freq=time_step)
        
          
        
        
    def __get_xml_coefficients(self):
        
        """
        
        Retrieves calibration coefficients for sensors detected in xml configuration file (.xmlcon) and
        stores them in self._coefficients_xml.
        
        """
        
        # Dictionary of all possible sensors (as they appear in xml) and their calibration coefficients (the ones you want).
        sensor_coefficients = \
        {
        'TemperatureSensor': ['A0','A1','A2','A3'],
        'ConductivitySensor': ['G','H','I','J','CPcor','CTcor'],
        'PressureSensor': ['PA0','PA1','PA2','PTEMPA0','PTEMPA1','PTEMPA2','PTCA0','PTCA1','PTCA2','PTCB0','PTCB1','PTCB2'],
        'WET_LabsCStar': ['M','B', 'PathLength'],
        'OxygenSensor': ['A','B','C','D0','D1','D2','E','Tau20','H1','H2','H3','Soc','offset'],
        'TurbidityMeter': ['ScaleFactor','DarkVoltage']
        }
        
        tree = ET.parse(self._filepath_xml)
        root = tree.getroot()
        
        self._coefficients_xml = {}
        
        for sensor in self._sensors:
            
            self._coefficients_xml[sensor] = {}
            
            if sensor == 'ConductivitySensor':
                child = root.findall('Instrument/SensorArray/Sensor/ConductivitySensor/Coefficients')[1]
            
            elif sensor == 'OxygenSensor' and self._xmlcon['Name'] == 'SBE 19plus V2 Seacat CTD':
                child = root.findall('Instrument/SensorArray/Sensor/OxygenSensor/CalibrationCoefficients')[1]
                
            elif sensor == 'OxygenSensor' and self._xmlcon['Name'] == 'SBE 16plus V2 Seacat CTD':
                # Overwrite OxygenSensor coefficients if SBE16 (uses different DO sensor and calibration)
                sensor_coefficients['OxygenSensor'] = ['A0','A1','A2','B0','B1','C0','C1','C2', 'pcor']
                child = root.find('Instrument/SensorArray/Sensor/OxygenSensor')
            
            else:
                child = root.find(f'Instrument/SensorArray/Sensor/{sensor}')
            
            for coefficient in sensor_coefficients[sensor]:
                self._coefficients_xml[sensor][coefficient] = float(child.find(coefficient).text)


    def __get_hex_coefficients(self):
        
        """
        
        Retrieves calibration coefficients from SBE16/19 hex file (.hex) and stores them in self._coefficients_hex.
        
        """
        
        hex_file = open(self._filepath_hex, 'r')
        hex_header = hex_file.read()
        hex_file.close()

        hex_header = hex_header.split('*END*')[0]

        self._coefficients_hex = {
                                 'TemperatureSensor': {},
                                 'ConductivitySensor': {},
                                 'PressureSensor': {}
                                }

        self._coefficients_hex['TemperatureSensor']['A0'] = float(hex_header.split('<TA0>')[1].split('</TA0>')[0])
        self._coefficients_hex['TemperatureSensor']['A1'] = float(hex_header.split('<TA1>')[1].split('</TA1>')[0])
        self._coefficients_hex['TemperatureSensor']['A2'] = float(hex_header.split('<TA2>')[1].split('</TA2>')[0])
        self._coefficients_hex['TemperatureSensor']['A3'] = float(hex_header.split('<TA3>')[1].split('</TA3>')[0])

        self._coefficients_hex['ConductivitySensor']['G'] = float(hex_header.split('<G>')[1].split('</G>')[0])
        self._coefficients_hex['ConductivitySensor']['H'] = float(hex_header.split('<H>')[1].split('</H>')[0])
        self._coefficients_hex['ConductivitySensor']['I'] = float(hex_header.split('<I>')[1].split('</I>')[0])
        self._coefficients_hex['ConductivitySensor']['J'] = float(hex_header.split('<J>')[1].split('</J>')[0])
        self._coefficients_hex['ConductivitySensor']['CPcor'] = float(hex_header.split('<CPCOR>')[1].split('</CPCOR>')[0])
        self._coefficients_hex['ConductivitySensor']['CTcor'] = float(hex_header.split('<CTCOR>')[1].split('</CTCOR>')[0])

        self._coefficients_hex['PressureSensor']['PA0'] = float(hex_header.split('<PA0>')[1].split('</PA0>')[0])
        self._coefficients_hex['PressureSensor']['PA1'] = float(hex_header.split('<PA1>')[1].split('</PA1>')[0])
        self._coefficients_hex['PressureSensor']['PA2'] = float(hex_header.split('<PA2>')[1].split('</PA2>')[0])
        self._coefficients_hex['PressureSensor']['PTEMPA0'] = float(hex_header.split('<PTEMPA0>')[1].split('</PTEMPA0>')[0])
        self._coefficients_hex['PressureSensor']['PTEMPA1'] = float(hex_header.split('<PTEMPA1>')[1].split('</PTEMPA1>')[0])
        self._coefficients_hex['PressureSensor']['PTEMPA2'] = float(hex_header.split('<PTEMPA2>')[1].split('</PTEMPA2>')[0])
        self._coefficients_hex['PressureSensor']['PTCA0'] = float(hex_header.split('<PTCA0>')[1].split('</PTCA0>')[0])
        self._coefficients_hex['PressureSensor']['PTCA1'] = float(hex_header.split('<PTCA1>')[1].split('</PTCA1>')[0])
        self._coefficients_hex['PressureSensor']['PTCA2'] = float(hex_header.split('<PTCA2>')[1].split('</PTCA2>')[0])
        self._coefficients_hex['PressureSensor']['PTCB0'] = float(hex_header.split('<PTCB0>')[1].split('</PTCB0>')[0])
        self._coefficients_hex['PressureSensor']['PTCB1'] = float(hex_header.split('<PTCB1>')[1].split('</PTCB1>')[0])
        self._coefficients_hex['PressureSensor']['PTCB2'] = float(hex_header.split('<PTCB2>')[1].split('</PTCB2>')[0])
        
        
    def __compare_coefficients(self):

        """
        
        Compares calibration coefficients extracted from xml and hex file and warns user if they do not match.
        
        """
        
        for sensor in self._coefficients_hex:
            for coefficient in self._coefficients_hex[sensor]:
                rtol = abs(self._coefficients_xml[sensor][coefficient] * 0.001)
                if not np.isclose(self._coefficients_xml[sensor][coefficient], self._coefficients_hex[sensor][coefficient], rtol=rtol):
                    warnings.warn(f'*** WARNING *** : {sensor} calibration coefficient {coefficient} in xmlcon does not match corresponding value in hex file... Proceeding with value from xmlcon.')

    
    def __get_hex_samples(self):
        
        """
        
        Extracts hexadecimal measurements from SBE16/19 hex file. 
        
        """
        
        file_hex = open(self._filepath_hex, 'r')
        data_hex = file_hex.read()
        file_hex.close()
        
        self._hex_samples = data_hex.split('*END*')[1].strip().split('\n')
        
    def __parse_hexstr(self,x,start,end):
        """
        parse the hexadecimal string x from index start to end. assume it is 
        base 16 integer

        Parameters
        ----------
        x : string
            hex input string.
        start : int
            first character to parse
        end : int
            last_character to parse.

        Returns
        -------
        out : TYPE
            DESCRIPTION.

        """
        
        try:
            out = int(x[start:end], base=16)
        except:
            out = np.nan
        return out 
    
    
    def __hex2temperature(self):
        
        """
        
        Calculates temperature (degrees Celcius, C) from hexadecimal string.
        
        """
        
        A0 = self._coefficients_xml['TemperatureSensor']['A0']
        A1 = self._coefficients_xml['TemperatureSensor']['A1']
        A2 = self._coefficients_xml['TemperatureSensor']['A2']
        A3 = self._coefficients_xml['TemperatureSensor']['A3']
        
        temperature_decimal = np.array([int(x[:6], base=16) for x in self._hex_samples])
        MV = (temperature_decimal - 524288)/1.6e7
        R = ((MV*2.900e9) + 1.024e8) / (2.048e4 - (MV*2.0e5))
        temperature_degrees = 1/(A0 + A1*np.log(R) + A2*np.log(R)**2 + A3*np.log(R)**3) - 273.15
        
        self.data['Temperature (C)'] = temperature_degrees

    def __hex2time(self):
        global time_decimal
        time_decimal1 = np.array([self.__parse_hexstr(x,42,50) for x in self._hex_samples])
        
        #time_decimal = np.array([int(x[42:50],base = 16) for x in self._hex_samples])
        #print(time_decimal, time_decimal1)
        time = pd.to_datetime('01 Jan 2000')  + np.array([pd.Timedelta(t,'second') for t in time_decimal])
        
        self.time = time
        
    def __hex2conductivity(self):

        """
        
        Calculates conductivity (Simiens/meter, S/m) from hexadecimal string.
        
        """

        G = self._coefficients_xml['ConductivitySensor']['G']
        H = self._coefficients_xml['ConductivitySensor']['H']
        I = self._coefficients_xml['ConductivitySensor']['I']
        J = self._coefficients_xml['ConductivitySensor']['J']
        CPcor = self._coefficients_xml['ConductivitySensor']['CPcor']
        CTcor = self._coefficients_xml['ConductivitySensor']['CTcor']

        conductivity_decimal = np.array([int(x[6:12], base=16) for x in self._hex_samples])
        f = conductivity_decimal / 256 / 1000
        conductivity_spm = (G + H*(f**2)+ I*(f**3) + J*(f**4)) / (1 + CTcor*self.data['Temperature (C)'] + CPcor*self.data['Pressure (dbar)'])
        
        self.data['Conductivity (S/m)'] = conductivity_spm


    def __hex2pressure(self):

        """
        
        Calculates pressure (decibars, dbar) from hexadecimal string.
        
        """

        PA0 = self._coefficients_xml['PressureSensor']['PA0']
        PA1 = self._coefficients_xml['PressureSensor']['PA1']
        PA2 = self._coefficients_xml['PressureSensor']['PA2']
        PTEMPA0 = self._coefficients_xml['PressureSensor']['PTEMPA0']
        PTEMPA1 = self._coefficients_xml['PressureSensor']['PTEMPA1']
        PTEMPA2 = self._coefficients_xml['PressureSensor']['PTEMPA2']
        PTCA0 = self._coefficients_xml['PressureSensor']['PTCA0']
        PTCA1 = self._coefficients_xml['PressureSensor']['PTCA1']
        PTCA2 = self._coefficients_xml['PressureSensor']['PTCA2']
        PTCB0 = self._coefficients_xml['PressureSensor']['PTCB0']
        PTCB1 = self._coefficients_xml['PressureSensor']['PTCB1']
        PTCB2 = self._coefficients_xml['PressureSensor']['PTCB2']
        

    

        pressure_decimal = np.array([self.__parse_hexstr(x,12,18) for x in self._hex_samples])
        ptcv_decimal = np.array([self.__parse_hexstr(x,18,22) for x in self._hex_samples])
        
        y = ptcv_decimal / 13107
        t = PTEMPA0 + PTEMPA1*(y) + PTEMPA2*(y**2)
        x = pressure_decimal - PTCA0 - PTCA1*t - PTCA2*(t**2)
        n = (x*PTCB0) / (PTCB0 + PTCB1*t + PTCB2*(t**2))
        
        pressure_dbar = PA0 + PA1*n + PA2*(n**2)
        pressure_dbar = (pressure_dbar - 14.7) * 0.689476
        
        self.data['Pressure (dbar)'] = pressure_dbar


    def __hex2turbidity(self):
        
        """
        
        Calculates turbidity (Nephelometric turbidity, NTU) from hexadecimal string measured 
        by WET Labs ECO NTU turbidity sensor.
        
        """
        
        scale_factor = self._coefficients_xml['TurbidityMeter']['ScaleFactor']
        dark_voltage = self._coefficients_xml['TurbidityMeter']['DarkVoltage']
        #print(self._xmlcon['Name'], self._sensor_index['TurbidityMeter'])
        
        
        start_idx = 4*(self._sensor_index['TurbidityMeter'] - 3) + 22
        end_idx = start_idx + 4
        #print(start_idx, end_idx)
        
        turbidity_decimal = np.array([self.__parse_hexstr(x,start_idx,end_idx) for x in self._hex_samples])
        # if self._xmlcon['Name'] == 'SBE 16plus V2 Seacat CTD':
            
        #     turbidity_decimal = np.array([self.__parse_hexstr(x,26,30) for x in self._hex_samples])#np.array([int(x[26:30], base=16) for x in self._hex_samples])
            
        # elif self._xmlcon['Name'] == 'SBE 19plus V2 Seacat CTD':
            
        #     turbidity_decimal = np.array([self.__parse_hexstr(x,30,34) for x in self._hex_samples])#np.array([int(x[30:34], base=16) for x in self._hex_samples])
        
        turbidity_volt = turbidity_decimal / 13107
        turbidity_ntu = scale_factor * (turbidity_volt - dark_voltage)
        
        self.data['Turbidity (NTU)'] = turbidity_ntu
        
        
    def __hex2transmission(self):
        
        """
        
        Calculates light transmission (%) and beam attenuation coefficients from hexadecimal string measured 
        by WET Labs C-Star transmissometer.
        
        """
        
        M = self._coefficients_xml['WET_LabsCStar']['M']
        B = self._coefficients_xml['WET_LabsCStar']['B']
        z = self._coefficients_xml['WET_LabsCStar']['PathLength']
        
        start_idx = 4*(self._sensor_index['WET_LabsCStar'] - 3) + 22
        end_idx = start_idx + 4
        #print(start_idx, end_idx)
        
        transmission_decimal = np.array([self.__parse_hexstr(x,start_idx,end_idx) for x in self._hex_samples])
        #transmission_decimal = np.array([self.__parse_hexstr(x,22,26) for x in self._hex_samples])#np.array([int(x[22:26], base=16) for x in self._hex_samples])
        transmission_volt = transmission_decimal / 13107
        
        beam_transmission = (M*transmission_volt) + B
        beam_attenuation = -(1/z)*np.log(beam_transmission/100)
        
        self.data['Light Transmission (%)'] = beam_transmission
        self.data['Beam Attenuation Coefficient'] = beam_attenuation
    
    
    def __hex2oxygen(self):
        
        """
        
        Calculates oxygen concentration (milliliters/Liter, mL/L) from hexadecimal string.
        For details on calculation of salinity correction factor (Scorr) see Appendix I of:
        https://www.seabird.com/asset-get.download.jsa?id=54627862513
        
        """
        start_idx = 4*(self._sensor_index['OxygenSensor'] - 3) + 22
        #end_idx = start_idx + 4
        #print(start_idx, end_idx)
        # SBE 63 Dissolved Oxygen Sensor calculations
        if self._xmlcon['Name'] == 'SBE 16plus V2 Seacat CTD':
            end_idx = start_idx + 6
            A0 = self._coefficients_xml['OxygenSensor']['A0']
            A1 = self._coefficients_xml['OxygenSensor']['A1']
            A2 = self._coefficients_xml['OxygenSensor']['A2']
            B0 = self._coefficients_xml['OxygenSensor']['B0']
            B1 = self._coefficients_xml['OxygenSensor']['B1']
            C0 = self._coefficients_xml['OxygenSensor']['C0']
            C1 = self._coefficients_xml['OxygenSensor']['C1']
            C2 = self._coefficients_xml['OxygenSensor']['C2']
            E = self._coefficients_xml['OxygenSensor']['pcor']
            
            T = self.data['Temperature (C)']
            P = self.data['Pressure (dbar)']
            S = self.data['Salinity (PSU)']  
            
            # Coefficients for salinity correction factor (Scorr)
            solB0 = -6.24523e-3; solB1 = -7.37614e-3; solB2 = -1.03410e-2; solB3 = -8.17083e-3
            solC0 = -4.88682e-7
            
            Ts = np.log((298.15-T)/(273.15+T))
            
            Scorr = np.exp(S*(solB0+(solB1*Ts)+(solB2*(Ts**2))+(solB3*(Ts**3))) + (solC0*(S**2)))
            
            

            oxygen_decimal = np.array([self.__parse_hexstr(x,start_idx,end_idx) for x in self._hex_samples])#np.array([int(x[30:36], base=16) for x in self._hex_samples])
            
            
            #oxygen_decimal = np.array([self.__parse_hexstr(x,30,36) for x in self._hex_samples])#np.array([int(x[30:36], base=16) for x in self._hex_samples])
            
            V = ((oxygen_decimal/100000)-10) / 39.457071 

            eqpt1 = ((A0+(A1*T)+(A2*(V**2))) / (B0+(B1*V))) - 1
            eqpt2 = C0+(C1*T)+(C2*(T**2))
            eqpt3 = np.exp(E*P/(T+273.15))
            
            oxygen_conc = (eqpt1/eqpt2)*eqpt3*Scorr
            
            self.data['Oxygen (ml/l)'] = oxygen_conc
        
        # SBE 43 Dissolved Oxygen Sensor calculations
        elif self._xmlcon['Name'] == 'SBE 19plus V2 Seacat CTD':
            end_idx = start_idx + 4
            A = self._coefficients_xml['OxygenSensor']['A']
            B = self._coefficients_xml['OxygenSensor']['B']
            C = self._coefficients_xml['OxygenSensor']['C']
            #D0 = self._coefficients_xml['OxygenSensor']['D0']
            #D1 = self._coefficients_xml['OxygenSensor']['D1']
            #D2 = self._coefficients_xml['OxygenSensor']['D2']
            E = self._coefficients_xml['OxygenSensor']['E']
            #Tau20 = self._coefficients_xml['OxygenSensor']['Tau20']
            #H1 = self._coefficients_xml['OxygenSensor']['H1']
            #H2 = self._coefficients_xml['OxygenSensor']['H2']
            #H3 = self._coefficients_xml['OxygenSensor']['H3']
            Soc = self._coefficients_xml['OxygenSensor']['Soc']
            Voffset = self._coefficients_xml['OxygenSensor']['offset']
            
            T = self.data['Temperature (C)']
            P = self.data['Pressure (dbar)']
            
            
            oxygen_decimal = np.array([self.__parse_hexstr(x,start_idx,end_idx) for x in self._hex_samples])
            #oxygen_decimal = np.array([self.__parse_hexstr(x,26,30) for x in self._hex_samples])#np.array([int(x[26:30], base=16) for x in self._hex_samples])
            
            V = oxygen_decimal / 13107
            
            eqpt1 = Soc*(V+Voffset)*(1+(A*T)+(B*(T**2))+(C*(T**3)))
            eqpt2 = np.exp(E*P/(T+273.15))
            oxysat = self.__oxygen_saturation()
            
            oxygen_conc = eqpt1*eqpt2*oxysat
            
            self.data['Oxygen (ml/l)'] = oxygen_conc
    
    
    def __conductivity2salinity(self):
        
        """
        
        Calculates salinity (PSU) from conductivity following the standards of the Practical Salinity Scale - 1978 (PSS-78)
        For details on calculation see:
        https://salinometry.com/pss-78/
        https://www.seabird.com/asset-get.download.jsa?id=54627861526
        
        """
        
        a = [0.008, -0.1692, 25.3851, 14.0941, -7.0261, 2.7081]
        b = [0.0005, -0.0056, -0.0066, -0.0375, 0.0636, -0.0144]
        k = 0.0162
        
        A1 = 2.07e-5; A2 = -6.37e-10; A3 = 3.989e-15
        B1 = 3.426e-2; B2 = 4.464e-4; B3 = 4.215e-1; B4 = -3.107e-3
        C0 = 6.766097e-1; C1 = 2.00564e-2; C2 = 1.104259e-4; C3 = -6.9698e-7; C4 = 1.0031e-9
        
        T = self.data['Temperature (C)'] * 1.00024      # Temperature IPTS-68, C
        P = self.data['Pressure (dbar)']                # Pressure, dbars
        R = self.data['Conductivity (S/m)'] / 4.2914    # Conductivity ratio (C of water at 35 PSU and 15C @ sea-level = 4.2914 S/m)
        
        Rp = 1 + (((A1*P)+(A2*(P**2))+(A3*(P**3)))/(1+(B1*T)+(B2*(T**2))+(B3*R)+(B4*T*R)))
        rT = C0 + (C1*T) + (C2*(T**2)) + (C3*(T**3)) + (C4*(T**4))
        RT = R/(Rp*rT)
        
        S1 = 0; S2 = 0
        for i in range(6):
            S1 += a[i] * np.power(RT,(i/2))
            S2 += b[i] * np.power(RT,(i/2))
        
        S = S1 + (((T-15)/(1+(k*(T-15))))*S2)
        
        self.data['Salinity (PSU)'] = S
       
        
    def __oxygen_saturation(self):
        
        """
        
        Calculates the oxygen saturation limit (mL/L) as a function of temperature and salinity 
        For details see Appendix A of:
        http://www.argodatamgt.org/content/download/26535/181243/file/SBE43_ApplicationNote64_RevJun2013.pdf
        
        Returns:
            oxysat (np.array): oxygen saturation limit (mL/L)
        
        """
        
        A0 = 2.00907; A1 = 3.22014; A2 = 4.0501; A3 = 4.94457; A4 = -0.256847; A5 = 3.88767
        B0 = -0.00624523; B1 = -0.00737614; B2 = -0.010341; B3 = -0.00817083
        C0 = -4.88682e-7
        
        T = self.data['Temperature (C)']
        S = self.data['Salinity (PSU)']
        
        Ts = np.log((298.15-T)/(273.15+T))
        
        eqpt1 = A0+(A1*Ts)+(A2*(Ts**2))+(A3*(Ts**3))+(A4*(Ts**4))+(A5*(Ts**5))
        eqpt2 = (S*(B0+(B1*Ts)+(B2*(Ts**2))+(B3*(Ts**3)))) + (C0*(S**2))
        
        oxysat = np.exp(eqpt1+eqpt2)
        
        return oxysat
        
            

        
        
        return df
        
#%%




#%%  

class DataSet(seabird_ctd):
    """
  A derived class from seabird_ctd to enhance data handling and analytics specific 
  to sea-bird conductivity, temperature, and depth (CTD) instruments.

  This class integrates additional functionalities for plotting, geometric calculations,
  data processing, and masking operations on top of the base functionalities provided
  by the seabird_ctd class.

  Attributes:
      plot (__Plotting): An instance of the nested __Plotting class for handling data visualization.
      name (str): The filename extracted from the filepath_hex, used as an identifier.
      geometry (__Geometry): An instance of the nested __Geometry class for managing sensor geometry.
      mask (__Masking): An instance of the nested __Masking class for applying masks to the data.
      processing (__Processing): An instance of the nested __Processing class for additional data processing tasks.

  Parameters:
      filepath_hex (str): Path to the hexadecimal data file from the CTD instrument.
      filepath_xml (str): Path to the XML configuration file associated with the CTD data.
      **kwargs: Arbitrary keyword arguments that can be passed to the seabird_ctd constructor.

  Methods:
      get_timeseries_data(field_name='Turbidity (NTU)', mask=True): Retrieves timeseries data for a specified field.

     """   
    def __init__(self,filepath_hex, filepath_xml,**kwargs):
        super().__init__(filepath_hex, filepath_xml)
        self.plot = self.__Plotting(self)
        self.name = filepath_hex.split(os.sep)[-1]
        self.geometry = self.__Geometry(self)
        self.mask = self.__Masking(self)
        self.processing = self.__Processing(self)
        self.timezone_correction = 0

        
    def get_timeseries_data(self, field_name='Turbidity (NTU)', mask=True):
        """
        Retrieve timeseries data for a given field name.
    
        Parameters:
        - field_name (str): Name of the field for which timeseries data is retrieved (default: 'Turbidity (NTU)').
        - mask (bool): If True, any defined masks will be applied to the data (default: True).
    
        Returns:
        - t (numpy.ndarray): DateTime array representing the time values.
        - x (numpy.ndarray): Timeseries data array for the specified field_name.
        """
        t = self.data['DateTime'].copy() + pd.to_timedelta(f'{self.timezone_correction}h') #apply timezone correction
        x = self.data[field_name].copy()
    
        if mask: # apply masks 
            x = self.mask.apply_masks(x)
    
        return t, x
    
    def to_csv(self):
        
        df = self.to_pandas_df()
        
        df['DateTime'] = df['DateTime'] + pd.to_timedelta(f'{self.timezone_correction}h') #apply timezone correction
        
        filename_hex = os.path.basename(self._filepath_hex)
        filename_csv = os.path.splitext(filename_hex)[0] + '.csv'
        
        df.to_csv(filename_csv)
        
    def to_pandas_df(self, mask=True):
        df = pd.DataFrame.from_dict(self.data)
        df['DateTime'] = df['DateTime'] + pd.to_timedelta(f'{self.timezone_correction}h') #apply timezone correction
        df.set_index('DateTime',drop = True,inplace = True)
        
        return df
        
    class __Processing:
        """
        Manage data processing functionality for CTD data.
    
        Parameters
        ----------
        ctd : CTD
            CTD (Conductivity, Temperature, Depth) object.
    
        Methods
        -------
        calculate_depth(environment='SALTWATER')
            Calculate depth from pressure following SBE APPLICATION NOTE NO. 69.
    
        Attributes
        ----------
        _ctd : CTD
            CTD object containing data for processing.
        """
    
        def __init__(self, ctd):
            self._ctd = ctd
            
            
        def calculate_SSC(self, A=1):
            """
            Calculates Suspended Solids Concentration (SSC) from turbidity data.
        
            Parameters:
            - self (object): Instance of the class containing CTD data.
            - A (float): Conversion factor from Turbidity (NTU) to SSC.
        
            Returns:
            None. Updates the CTD data with the calculated SSC values.
            """
            # convert from turbidity (NTU) to suspended solids concentration assuming SSC = A * NTU
            self._ctd.data['SSC (mg/L)'] = A * self._ctd.data['Turbidity (NTU)']
            
    
        def calculate_depth(self, environment='SALTWATER'):
            """
            Calculate depth from pressure following SBE APPLICATION NOTE NO. 69.
    
            Sea-Bird uses the formula in UNESCO Technical Papers in Marine Science
            No. 44. This is an empirical formula that takes compressibility (that is,
            density) into account. An ocean water column at 0 °C (t = 0) and 35 PSU
            (s = 35) is assumed.
            
            If latitude has not been calculated in the position
            dataset, then both latitude and longitude will be calculated 
            automatically
    
            Parameters
            ----------
            environment : str, optional
                Specify whether the CTD is in "SALTWATER" or "FRESHWATER".
                The default is 'SALTWATER'.
    
            Returns
            -------
            None
            """
            
            

    
            p = self._ctd.data['Pressure (dbar)'] # Pressure
            latitude = self._ctd.geometry.pose.pose['latitude'].to_numpy()  # 
            x = np.sin(latitude / 57.29578) ** 2
            g = (9.780318) * (1.0 + ((5.2788e-3) + (2.36e-5) * x) * x) + (1.092e-6) * p  # Gravity variation with latitude and pressure
            d = (((( (-1.82e-15) * p + 2.279e-10) * p - 2.2512e-5) * p + 9.72659) * p) / g
            self._ctd.data['Depth (m)'] = d  # Update the data dictionary
                
            
        def calculate_density(self):
            """
            Calculate the density of seawater using UNESCO 1983 polynomial equations of state.
            
            Validated agaist this online calucator https://www.phys.ocean.dal.ca/~kelley/seawater/density.html
            Parameters:
            - s : numpy.ndarray
                Salinity in Practical Salinity Units (PSU).
            - t : numpy.ndarray
                Temperature in degrees Celsius.
            - p : numpy.ndarray
                Pressure in decibars.
            
            Returns:
            - numpy.ndarray
                Density of seawater.
            """
            t = np.array(self._ctd.data['Temperature (C)'])
            p = np.array(self._ctd.data['Pressure (dbar)'])
            s = np.array(self._ctd.data['Salinity (PSU)'])
            
            A0 = 999.842594
            A1 = 6.793952e-2
            A2 = -9.095290e-3
            A3 = 1.001685e-4
            A4 = -1.120083e-6
            A5 = 6.536332e-9
            
            B0 = 8.24493e-1
            B1 = -4.0899e-3
            B2 = 7.6438e-5
            B3 = -8.2467e-7
            B4 = 5.3875e-9
            
            C0 = -5.72466e-3
            C1 = 1.0227e-4
            C2 = -1.6546e-6
            
            D0 = 4.8314e-4
            
            
            
            FQ0 = 54.6746
            FQ1 = -0.603459
            FQ2 = 1.09987e-2
            FQ3 = -6.1670e-5
            
            G0 = 7.944e-2
            G1 = 1.6483e-2
            G2 = -5.3009e-4
            
            i0 = 2.2838e-3
            i1 = -1.0981e-5
            i2 = -1.6078e-6
            
            J0 = 1.91075e-4
            
            M0 = -9.9348e-7
            M1 = 2.0816e-8
            M2 = 9.1697e-10
            
            E0 = 19652.21
            E1 = 148.4206 #c
            E2 = -2.327105
            E3 = 1.360477e-2
            E4 = -5.155288e-5
            
            H0 = 3.239908
            H1 = 1.43713e-3
            H2 = 1.16092e-4
            H3 = -5.77905e-7
            
            K0 = 8.50935e-5
            K1 = -6.12293e-6
            K2 = 5.2787e-8
            
            t2 = t * t
            t3 = t * t2
            t4 = t * t3
            t5 = t * t4
            
            #s = np.maximum(s, 0.000001)  # Avoid division by zero
            
            s32 = np.power(s, 1.5)
            
            p = p/10.0  # convert decibars to bars
            
            sigma = A0 + A1*t + A2*t2 + A3*t3 + A4*t4 + A5*t5+ (B0 + B1*t + B2*t2 + B3*t3 + B4*t4)*s+ (C0 + C1*t + C2*t2)*s32 + D0*s*s
            
            kw = E0 + E1*t + E2*t2 + E3*t3 + E4*t4
            aw = H0 + H1*t + H2*t2 + H3*t3
            bw = K0 + K1*t + K2*t2
            
            k = kw + (FQ0 + FQ1*t + FQ2*t2 + FQ3*t3)*s + (G0 + G1*t + G2*t2)*s32+ (aw + (i0 + i1*t + i2*t2)*s + (J0*s32))*p + (bw + (M0 + M1*t + M2*t2)*s)*p*p
            
            val = 1.0-(p/k)
            
            sigma = (sigma/val) #- 1000
                # non_zero_mask = val != 0.0
                # sigma[non_zero_mask] = sigma[non_zero_mask] / val[non_zero_mask] - 1000.0
            self._ctd.data['Density (kg/m3)'] = sigma


    class __Geometry:
        """
        Manage the geometry (position, orientation, etc...) of an instrument.
    
        Parameters
        ----------
        ctd : CTD
            CTD (Conductivity, Temperature, Depth) object.
    
        Attributes
        ----------
        relative_position : numpy array
            Position of the sensor relative to the position measurement for the instrument.
        Pose : Pose
            Pose object containing the instrument's position and orientation at all timestamps.
    
        Methods
        -------
        set_Pose(Pose)
            Define the instrument pose (position and orientation) with a Pose object.
    
        set_sensor_relative_geometry(rotation=0, offset=(0, 0, 0))
            Calculate the x, y, z position of the sensor in the coordinate reference frame of the instrument.
    
        get_absolute_sensor_position()
            Calculate the absolute position of the sensor, taking into account the position and orientation of the platform.
        """
    
        def __init__(self, ctd):
            self._ctd = ctd
            self.relative_position = np.zeros(3, dtype=float)
            self.pose = None
    
        def set_pose(self, Pose, update_depth = False,**kwargs):
            """
            Define the instrument pose (position and orientation) with a 
            Pose object. Makes a cope of the pose object and stores it under 
            ctd.geometry.Pose
            
            Parameters
            ----------
            Pose : Pose
                Pose object containing position and orientation information.
            update_depth : bool, optional 
                If True, the calculated depth (from ctd pressure) will be used
                as the pose z variable data. 
    
            Returns
            -------
            None
            """
            
            
            
            
            
            # copy input object and Resample the input timeseries to the CTD measurement timesteps.
            self.pose = copy.deepcopy(Pose)
            
            # ## infer the best tolerance 
            # t = self._ctd.data['DateTime'].to_numpy()
            # dt = np.diff(t,prepend = t[0],).astype(float)/1e9 # time delta in seconds
            # tolerance = 1.01*np.percentile(dt,99) # mask to identify data gaps 
            # print(tolerance)
            
            
            self.pose.resample_to(self._ctd.data['DateTime'],kwargs)
    
            if not self.pose.pose.get('latitude'):
                self._ctd.geometry.pose.add_lat_lon()

            
            # update pose z variable with calculated depth from ctd data
            if update_depth:
                # calculate latitude and longitude if needed
                # if not self.pose.pose.get('latitude'):
                #     self._ctd.geometry.pose.add_lat_lon()
                self._ctd.geometry.pose.add_lat_lon()
                # calculate depth (based on pressure and latitude)
                self._ctd.processing.calculate_depth()
                
                # resample input timeser
                self._ctd.geometry.pose.resample_from(pd.Series(-self._ctd.data['Depth (m)'], index =  self._ctd.data['DateTime']),field_name = 'z', z_convention = 'reverse')
                
                

                
            
            
    
        def set_sensor_relative_geometry(self, rotation=0, offset=(0, 0, 0)):
            """
            Calculate the x, y, z position of the sensor in the coordinate reference frame of the instrument.
    
            Parameters
            ----------
            rotation : float, optional
                Rotation angle (in degrees) of the sensor.
                The default is 0.
    
            offset : numpy array, optional
                x, y, z offsets for the instrument. This offset should be the relative distance between the
                position measurement (e.g., from the vessel GPS) and the center of the sensor.
                The default is (0, 0, 0).
    
            Returns
            -------
            None
            """
            self.relative_position = np.array(offset, dtype=float)  # Position of the sensor relative to the instrument.
    
        def get_absolute_sensor_position(self):
            """
            Calculate the absolute position of the sensor, taking into account the position and orientation
            of the platform (e.g., ROV), and the relative position of the sensor on the platform.
    
            Returns
            -------
            absolute_position: numpy array
                numpy array containing the (x, y, z) position of the sensor for every timestep.
            """
            # Get position of beam midpoints for every ensemble.
            X = np.empty((3, self._ctd.n_samples))
            pose = self.pose.pose
    
            for i in range(self._ctd.n_samples):
                # Build rotation matrix.
                yaw = pose['heading'].to_numpy()[i]
                pitch = pose['pitch'].to_numpy()[i]
                roll = pose['roll'].to_numpy()[i]
                R = np.dot(ptools.gen_rot_x(roll), ptools.gen_rot_z(yaw).dot(ptools.gen_rot_y(pitch)))  # 3-d rotation operator
                Xp = np.add(pose[['x', 'y', 'z']].to_numpy().T[:, i], self.relative_position.T.dot(R)).T  # Apply rotation to sensor relative orientation vector
                X[:, i] = Xp  # Update position for the current sample
    
            # Apply masks (for x, y, z coordinates).
            X[0] = self._ctd.mask.apply_masks(X[0])
            X[1] = self._ctd.mask.apply_masks(X[1])
            X[2] = self._ctd.mask.apply_masks(X[2])
    
            return X
            
    
    class __Plotting:
        """
        Manage plotting functionality for CTD data.
    
        Parameters
        ----------
        ctd : CTD
            CTD (Conductivity, Temperature, Depth) object.
    
        Methods
        -------
        timeseries(field_name='Turbidity (NTU)')
            Create a timeseries plot of CTD data.
    
        Attributes
        ----------
        _ctd : CTD
            CTD object containing data for plotting.
        """
    
        def __init__(self, ctd):
            self._ctd = ctd
    
        def timeseries(self, field_name='Turbidity (NTU)',mask = True):
            """
            Create a timeseries plot of CTD data.
    
            Parameters
            ----------
            field_name : str, optional
                Name of the field to plot. Any key in the CTD data dictionary or 'all' to plot all fields in subplots.
                The default is 'Turbidity (NTU)'. 
            mask: bool, optional
                if True, masks will be applied to the data (default). If false, raw data will be plotted. 
            Returns
            -------
            fig : matplotlib.figure.Figure
                Matplotlib figure object.
    
            ax : matplotlib.axes._axes.Axes
                Matplotlib axes object.
            """
            
            #if field_name == 'all':
            
            
            
            fig, ax = plt.subplots(figsize=(10, 4))
            x,y = self._ctd.get_timeseries_data(field_name=field_name,mask = mask)
            ax.plot(x, y, lw=1)
            ax.set_ylabel(field_name)
            ax.set_xlabel('Time')
    
            xlims = mdates.date2num(x)
    
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M %d%b%y '))
            ax.grid(alpha=0.1)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=0, ha='center')
            ax.xaxis.tick_bottom()
            ax.xaxis.set_label_position('bottom')
            
            title = self._ctd._filepath_hex.split(os.sep)[-1] + '\n' + self._ctd._filepath_xml.split(os.sep)[-1]
            ax.set_title(title, fontsize = 7)
    
            return fig, ax
                
            
    class __Masking:
        """
        Manage masking functionality for CTD data.
    
        Parameters
        ----------
        ctd : CTD
            CTD (Conductivity, Temperature, Depth) object.
    
        Attributes
        ----------
        _ctd : CTD
            CTD object containing data for masking.
        masks : dict
            Dictionary to hold masks for ensemble data.
        mask_status : dict
            Dictionary to hold activation status of defined masks.
    
        Methods
        -------
        define_mask(mask, name, set_active=False)
            Define a boolean mask that can be applied to timeseries data.
            
        set_mask_status(status, name='all')
            Change the status of a mask, or multiple masks.
            
        apply_masks(X)
            Apply all active masks to the ensemble array X.
        """
    
        def __init__(self, ctd):
            self._ctd = ctd
            self.masks = {}  # Dictionary to hold masks for ensemble data
            self.mask_status = {}  # Dictionary to hold activation status of defined masks
    
        def define_mask(self, mask, name, set_active=False):
            """
            Define a boolean mask that can be applied to timeseries data.
    
            Parameters
            ----------
            mask : numpy array
                Numpy array with dimensions (n_samples).
            name : str
                Name for the mask.
            set_active : bool, optional
                If True, the defined mask will be activated.
                Default is False.
    
            Returns
            -------
            None
            """
            # Check that mask has correct dimensions
            valid_dims = (self._ctd.n_samples)
            if not np.shape(mask) == valid_dims:
                ValueError(f'Mask must have dimensions of {valid_dims}')
    
            self.masks[name] = mask
    
            # Initialize the mask status
            if set_active:
                self.mask_status[name] = True
            else:
                self.mask_status[name] = False
    
        def set_mask_status(self, status, name='all'):
            """
            Change the status of a mask, or multiple masks.
            The ensemble data corresponding to FALSE entries in the mask will be converted to np.nan.
    
            Parameters
            ----------
            name : str or list of str, optional
                Mask name, or list of mask names. If 'all', all defined masks will be activated.
                The default is 'all'.
            status : bool
                New status for the mask(s).
    
            Raises
            ------
            ValueError
                Invalid mask name.
    
            Returns
            -------
            None
            """
            if name == 'all':
                for key in self.masks.keys():
                    self.mask_status[key] = status
            elif type(name) == list:
                for n in name:
                    # Check if mask exists
                    if n in self.masks.keys():
                        self.mask_status[n] = status
                    else:
                        raise ValueError(f'{n} is not a defined mask.')
            elif type(name) == str:
                if name in self.masks.keys():
                    self.mask_status[name] = status
                else:
                    raise ValueError(f'{name} is not a defined mask.')
    
        def apply_masks(self, X):
            """
            Apply all of the active masks to the ensemble array X.
            Masked values will be converted to np.nan.
    
            Parameters
            ----------
            X : numpy array
                Array of ensemble data with dimensions (n_bins, n_ensembles).
    
            Returns
            -------
            X : numpy array
                Masked array of ensemble data with dimensions (n_bins, n_ensembles).
            """
            if self.masks:
                for mask_name in self.masks.keys():
                    if self.mask_status[mask_name]:
                        mask = self.masks[mask_name]
                        np.putmask(X, ~mask, values=np.nan)
    
            return X
    

#%%


# hex_fpath = r'P:\41806287\41806287 NORI-D Data\Data\ROV\Hidden Gem\CTD\Raw\ROVDive20220921\DHIDive4_220921_1.hex'
# xmlcon_fpath = r'P:\41806287\41806287 NORI-D Data\Data\ROV\Hidden Gem\CTD\Raw\ROVDive20220921\DHIDIVE4_220921_1.xmlcon'
# ctd1 = seabird_ctd(filepath_hex = hex_fpath, filepath_xml = xmlcon_fpath)
# print(ctd1._sensor_index)

# hex_fpath = r'P:\41806287\41806287 NORI-D Data\Data\ROV\Island Pride\CTD\Raw\ROV_CTD_09102022\SBE19plus_01907947_2022_10_09_0005.hex'
# xmlcon_fpath = r'P:\41806287\41806287 NORI-D Data\Data\ROV\Island Pride\CTD\Config\SBE19-7947_DO-1900_CStar-1917_NTU-5874_xmiss_DO_swap.xmlcon'
# ctd2 = seabird_ctd(filepath_hex = hex_fpath, filepath_xml = xmlcon_fpath)
# print(ctd2._sensor_index)
#ctd = DataSet(filepath_hex = hex_fpath, filepath_xml = xmlcon_fpath)
#%
#%%
# tree = ET.parse(ctd._filepath_xml)
# root = tree.getroot()



# sensors = {}

# for sensor in root.findall('Instrument/SensorArray/'):
#     for s1 in sensor:
#         sensors[s1.tag] = {}
        
        
#         #sensors['Sen'] = 
#         #{'SensorID': '38'}
#         print(s1.attrib)
#         for s2 in s1:
#             sensors[s1.tag][s2.tag] = {}
#             for s3 in s2:
#                 print(s1.tag,s2.tag,s3.tag)
#                 sensors[s1.tag][s2.tag][s3.tag] = s3.text #pd.to_numeric(s3.text)
        
        
        # print(sensor.attrib)
        # print(child)

#%% read the xmlcon to get sensor order 





#%%

# xml_filepath = r'\\USDEN1-STOR.DHI.DK\\Projects\\41806287\\41806287 NORI-D Data\\Data\\ROV\\Island Pride HD14\\CTD\\Raw\\ROV_CTD_07102022\\Configuration\\SBE19-7947_DO-1900_CStar-1917_NTU-5874_xmiss_DO_swap.xmlcon'
# hex_filepath = r'\\USDEN1-STOR.DHI.DK\\Projects\\41806287\\41806287 NORI-D Data\\Data\\ROV\\Island Pride HD14\\CTD\\Raw\\ROV_CTD_27102022\\SBE19plus_01907947_2022_10_27_0026.hex'
# ctd = DataSet(hex_filepath,xml_filepath)

# x,t = ctd.get_timeseries_data()

# mask = (x>0.2)
# ctd.mask.define_mask(mask = mask, name = 'turbidity',set_active = True)


# ctd.plot.timeseries_plot()


# def main():     
    
#     scriptpath = os.path.abspath('.')
    
#     relpath_xml = 'ROV CTD/Config/SBE19-7947_DO-1900_CStar-1917_NTU-5874_xmiss_DO_swap.xmlcon'
#     #relpath_xml = 'FBCT1 CTD/Config/16-50406.xmlcon'
#     #relpath_xml = 'DeckSamplingSBE/DECKSMPL_RETURN03.XMLCON'

#     relpath_hex = 'ROV CTD/Raw/SBE19plus_01907947_2022_10_19_0001.hex'
#     #relpath_hex = 'FBCT1 CTD/Raw/SBE16plus_01650406_2022_10_04.hex'
#     #relpath_hex = 'DeckSamplingSBE/decksmpl_return03.hex'
    
#     filepath_xml = os.path.join(scriptpath,relpath_xml)
#     filepath_hex = os.path.join(scriptpath,relpath_hex)
    
#     test = SeabirdCTD(filepath_hex, filepath_xml)
    
#     #print(test.number_samples)
#     #print(test.data)
#     #print(test.coefficients_xml)
#     #test.dataframe2csv()
    
# ###############################################################################

# if __name__ == '__main__':
#     main()
    
###############################################################################
