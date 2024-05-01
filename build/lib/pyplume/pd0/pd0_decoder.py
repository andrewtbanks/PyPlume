# -*- coding: utf-8 -*-
"""
Created on Wed Jul 19 15:24:17 2023

@author: anba
"""

import struct,os,sys,time,datetime


import numpy as np
import re

#sys.path.insert(1, r'C:\Users\anba\Desktop\Projects\pyplume\pyplume\ptools')
#import ptools


# # # from plotting import plotting
# # # from processing import processing
# # # from geometry import geometry
# # # from masking import masking
# # # from PT3 import PT3


from ..ptools import ptools
from .plotting import plotting
from .processing import processing
from .geometry import geometry
from .masking import masking
from .PT3 import PT3



#%% Data formats from 

# WorkHorse Commands and Output Data Format

ensemble_header_format = (  
    ('HEADER ID',1,'<','B',True),
    ('DATA SOURCE ID',1,'<','B',True),
    ('N BYTES IN ENSEMBLE',2,'<','H',True),
    ('SPARE',1,'<','B',True),
    ('N DATA TYPES',1,'<','B',True),
)


fixed_leader_format = (
    ('FIXED LEADER ID',2,'<','H',True),
    ('CPU F/W VER.',1,'<','B',True),
    ('CPU F/W REV.',1,'<','B',True),
    ('SYSTEM CONFIGURATION',2,'<','B',False),
    ('REAL/SIM FLAG',1,'<','B',True),
    ('LAG LENGTH',1,'<','B',True),
    ('NUMBER OF BEAMS',1,'<','B',True),
    ('NUMBER OF CELLS {WN}',1,'<','B',True),
    ('PINGS PER ENSEMBLE {WP}',2,'<','H',True),
    ('DEPTH CELL LENGTH {WS}',2,'<','H',True),
    ('BLANK AFTER TRANSMIT {WF}',2,'<','H',True),
    ('PROFILING MODE {WM}',1,'<','B',True),
    ('LOW CORR THRESH {WC}',1,'<','B',True),
    ('NO. CODE REPS',1,'<','B',True),
    ('%GD MINIMUM {WG}',1,'<','B',True),
    ('ERROR VELOCITY MAXIMUM {WE}',2,'<','H',True),
    ('TPP MINUTES',1,'<','B',True),
    ('TPP SECONDS',1,'<','B',True),
    ('TPP HUNDREDTHS {TP}',1,'<','B',True),
    ('COORDINATE TRANSFORM {EX}',1,'<','B',False),
    ('HEADING ALIGNMENT {EA}',2,'<','H',True),
    ('HEADING BIAS {EB}',2,'<','H',True),
    ('SENSOR SOURCE {EZ}',1,'<','B',True),
    ('SENSORS AVAILABLE',1,'<','B',True),
    ('BIN 1 DISTANCE',2,'<','H',True),
    ('XMIT PULSE LENGTH BASED ON {WT}',2,'<','H',True),
    ('starting cell WP REF LAYER AVERAGE {WL} ending cell',2,'<','B',True),
    ('FALSE TARGET THRESH {WA}',1,'<','B',True),
    ('SPARE1',1,'<','B',False),
    ('TRANSMIT LAG DISTANCE',2,'<','H',True),
    ('CPU BOARD SERIAL NUMBER',8,'<','Q',False),
    ('SYSTEM BANDWIDTH {WB}',2,'<','H',True),
    ('SYSTEM POWER {CQ}',1,'<','B',True),
    ('SPARE2',1,'<','B',False),
    ('INSTRUMENT SERIAL NUMBER',4,'<','I',True),
    ('BEAM ANGLE',1,'<','B',True)
)


variable_leader_format = (
    ('VARIABLE LEADER ID',2,'<','H',True),
    ('ENSEMBLE NUMBER',2,'<','H',True),
    ('RTC YEAR {TS}',1,'<','B',True),
    ('RTC MONTH {TS}',1,'<','B',True),
    ('RTC DAY {TS}',1,'<','B',True),
    ('RTC HOUR {TS}',1,'<','B',True),
    ('RTC MINUTE {TS}',1,'<','B',True),
    ('RTC SECOND {TS}',1,'<','B',True),
    ('RTC HUNDREDTHS {TS}',1,'<','B',True),
    ('ENSEMBLE # MSB',1,'<','B',True),
    ('BIT RESULT',2,'<','H',True),
    ('SPEED OF SOUND {EC}',2,'<','H',True),
    ('DEPTH OF TRANSDUCER {ED}',2,'<','H',True),
    ('HEADING {EH}',2,'<','H',True),
    ('PITCH TILT 1 {EP}',2,'<','h',True),
    ('ROLL TILT 2 {ER}',2,'<','h',True),
    ('SALINITY {ES}',2,'<','H',True),
    ('TEMPERATURE {ET}',2,'<','h',True),
    ('MPT MINUTES',1,'<','B',True),
    ('MPT SECONDS',1,'<','B',True),
    ('MPT HUNDREDTHS',1,'<','B',True),
    ('HDG STD DEV',1,'<','B',True),
    ('PITCH STD DEV',1,'<','B',True),
    ('ROLL STD DEV',1,'<','B',True),
    ('ADC CHANNEL 0',1,'<','B',True),
    ('ADC CHANNEL 1',1,'<','B',True),
    ('ADC CHANNEL 2',1,'<','B',True),
    ('ADC CHANNEL 3',1,'<','B',True),
    ('ADC CHANNEL 4',1,'<','B',True),
    ('ADC CHANNEL 5',1,'<','B',True),
    ('ADC CHANNEL 6',1,'<','B',True),
    ('ADC CHANNEL 7',1,'<','B',True),
    ('ERROR STATUS WORD ESW {CY}',4,'<','I',True),
    ('SPARE1',2,'<','B',False),
    ('PRESSURE',4,'<','I',True),
    ('PRESSURE SENSOR VARIANCE',4,'<','I',True),
    ('SPARE2',1,'<','B',False),
    ('RTC CENTURY',1,'<','B',True),
    ('RTC YEAR',1,'<','B',True),
    ('RTC MONTH',1,'<','B',True),
    ('RTC DAY',1,'<','B',True),
    ('RTC HOUR',1,'<','B',True),
    ('RTC MINUTE',1,'<','B',True),
    ('RTC SECOND',1,'<','B',True),
    ('RTC HUNDREDTH',1,'<','B',True)
)


bottom_track_format = (
    ('BOTTOM-TRACK ID',2,'<','H',True),
    ('BT PINGS PER ENSEMBLE {BP}',2,'<','H',True),
    ('BT DELAY BEFORE RE-ACQUIRE {BD}',2,'<','H',True),
    ('BT CORR MAG MIN {BC}',1,'<','B',True),
    ('BT EVAL AMP MIN {BA}',1,'<','B',True),
    ('BT PERCENT GOOD MIN {BG}',1,'<','B',True),
    ('BT MODE {BM}',1,'<','B',True),
    ('BT ERR VEL MAX {BE}',2,'<','H',True),
    ('Reserved',4,'<','H',True),
    ('BEAM#1 BT RANGE',2,'<','H',True),
    ('BEAM#2 BT RANGE',2,'<','H',True),
    ('BEAM#3 BT RANGE',2,'<','H',True),
    ('BEAM#4 BT RANGE',2,'<','H',True),
    ('BEAM#1 BT VEL',2,'<','H',True),
    ('BEAM#2 BT VEL',2,'<','H',True),
    ('BEAM#3 BT VEL',2,'<','H',True),
    ('BEAM#4 BT VEL',2,'<','H',True),
    ('BEAM#1 BT CORR.',1,'<','H',True),
    ('BEAM#2 BT CORR.',1,'<','H',True),
    ('BEAM#3 BT CORR.',1,'<','H',True),
    ('BEAM#4 BT CORR.',1,'<','H',True),
    ('BEAM#1 EVAL AMP',1,'<','H',True),
    ('BEAM#2 EVAL AMP',1,'<','H',True),
    ('BEAM#3 EVAL AMP',1,'<','H',True),
    ('BEAM#4 EVAL AMP',1,'<','H',True),
    ('BEAM#1 BT %GOOD',1,'<','H',True),
    ('BEAM#2 BT %GOOD',1,'<','H',True),
    ('BEAM#3 BT %GOOD',1,'<','H',True),
    ('BEAM#4 BT %GOOD',1,'<','H',True),
    ('REF LAYER MIN {BL}',2,'<','H',True),
    ('REF LAYER NEAR {BL}',2,'<','H',True),
    ('REF LAYER FAR {BL}',2,'<','H',True),
    ('BEAM#1 REF LAYER VEL',2,'<','H',True),
    ('BEAM #2 REF LAYER VEL',2,'<','H',True),
    ('BEAM #3 REF LAYER VEL',2,'<','H',True),
    ('BEAM #4 REF LAYER VEL',2,'<','H',True),
    ('BM#1 REF CORR',1,'<','H',True),
    ('BM#2 REF CORR',1,'<','H',True),
    ('BM#3 REF CORR',1,'<','H',True),
    ('BM#4 REF CORR',1,'<','H',True),
    ('BM#1 REF INT',1,'<','H',True),
    ('BM#2 REF INT',1,'<','H',True),
    ('BM#3 REF INT',1,'<','H',True),
    ('BM#4 REF INT',1,'<','H',True),
    ('BM#1 REF %GOOD',1,'<','H',True),
    ('BM#2 REF %GOOD',1,'<','H',True),
    ('BM#3 REF %GOOD',1,'<','H',True),
    ('BM#4 REF %GOOD',1,'<','H',True),
    ('BT MAX. DEPTH {BX}',2,'<','H',True),
    ('BM#1 RSSI AMP',1,'<','H',True),
    ('BM#2 RSSI AMP',1,'<','H',True),
    ('BM#3 RSSI AMP',1,'<','H',True),
    ('BM#4 RSSI AMP',1,'<','H',True),
    ('GAIN',1,'<','H',True),
    ('*SEE BYTE 17',1,'<','H',True),
    ('*SEE BYTE 19',1,'<','H',True),
    ('*SEE BYTE 21',1,'<','H',True),
    ('*SEE BYTE 23',1,'<','H',True),
    ('RESERVED',4,'<','H',True),
)        

address_offsets_format = (None,2,'<','H',True)
data_ID_code_format = (None,2,'<','H',True)
echo_intensity_format= (None,1,'<','<H',True)
velocity_format = (None,2,'<','h',True)
coor_mag_format = (None,1,'<','H',True)
pct_good_format = (None,1,'<','H',True)


#%%
class Pd0:
    """
    A class for parsing and managing data from pd0 files, which are commonly used in
    oceanographic data collection with ADCP (Acoustic Doppler Current Profiler) instruments.

    This class provides functionality to read, process, validate, and access ensemble data
    from pd0 files. It includes methods for navigating through the data, retrieving specific
    ensembles, and extracting metadata and hydrodynamic measurements such as velocity and echo intensity.

    Attributes:
        _filepath (str): Path to the pd0 file being processed.
        _checksum (NoneType or bytearray): Checksum used for verifying the integrity of read data.
        _ensemble_rollover (int): Counter to manage the rollover of ensemble indices due to limitations in counting.
        _address_offsets (list of int): List of byte offsets for accessing specific data blocks within the file.
        ensemble_data (list of dicts): Parsed ensemble data stored as dictionaries.
        metadata (metadata): An instance of the nested metadata class containing detailed information about the file.

    Methods:
        __init__(filepath, **kwargs): Constructor for initializing a Pd0 instance.
        __get_first_and_last_ensembles(): Retrieves the first and last ensembles to determine the scope of the data.
        __skip_to_ensemble(n): Skips to a specified ensemble number within the file.
        __find_previous_ensemble(dist, maxiter, offset): Searches backwards to find the start of a valid ensemble.
        __find_next_ensemble(dist, maxiter, offset): Searches forwards to find the start of a valid ensemble.
        __check_valid_ensemble(ensemble): Checks the validity of an ensemble based on predefined criteria.
        __read_ensembles(start, end, print_progress): Reads a range of ensembles from the file.
        __read_ensemble(): Reads and parses a single ensemble from the file.
        __read_ensemble_header(): Reads and parses the header of an ensemble.
        __read_fixed_leader(): Reads and parses the fixed leader of an ensemble.
        __read_variable_leader(): Reads and parses the variable leader of an ensemble.
        __read_next_bytes(fmt): Reads bytes from the file according to a specified format.
        __get_LE_bit_string(byte): Converts a byte into a string of bits (little-endian).
        __parse_system_configuration(syscfg): Parses system configuration data.
        __parse_EX_command(ex): Parses coordinate transformation commands.
        write_pd0(fname): Writes parsed data back to a new pd0 file.
        __write_ensemble(ensemble): Writes a single ensemble's data to a file.
        __write_next_bytes(x, fmt): Writes data to a file in a specified byte format.
    """
    
    
    def __init__(self,filepath,**kwargs):

        
        self._filepath = filepath # filepath for general use across methods
        self._checksum = None # checksum for general use across methods
        self._ensemble_rollover = 0 # counter for ensemble rollover (at 65,536)
        self._address_offsets = [] # for general use across methods
        self.ensemble_data = []
        self.name = kwargs.pop('name',filepath.split(os.sep)[-1])
 
        class metadata:
            def __init__(self,pd0):
                #ef,el = pd0.__get_first_and_last_ensembles()
                self.filepath = filepath
                self.filesize= os.path.getsize(filepath)
                self.first_ensemble_in_file= ef['VARIABLE LEADER']['ENSEMBLE NUMBER']
                self.last_ensemble_in_file = el['VARIABLE LEADER']['ENSEMBLE NUMBER']
                
                
                self.ensemble_size = ef['ENSEMBLE HEADER']['N BYTES IN ENSEMBLE']
                
                self.first_date_in_file = self.__format_ensemble_datetime(ef)
                self.last_date_in_file = self.__format_ensemble_datetime(el)
                
                # ## calculate number of ensembles in the file
                # # case where the ensemble count rolled over in the file
                if self.first_ensemble_in_file > self.last_ensemble_in_file:
                     self.n_ensembles_in_file = (65536 - self.first_ensemble_in_file) + self.last_ensemble_in_file
                else:   
                    self.n_ensembles_in_file = self.last_ensemble_in_file - self.first_ensemble_in_file + 1   
                
            def __format_ensemble_datetime(self,ensemble):
                
                    century = str(ensemble['VARIABLE LEADER']['RTC CENTURY'])
                    if century == '0': century = '20' #Catch for UNKNOWN bug that occures when parsing DVS instruments
                    year = int(century + str(ensemble['VARIABLE LEADER']['RTC YEAR {TS}']))
                    month= ensemble['VARIABLE LEADER']['RTC MONTH {TS}']
                    day = ensemble['VARIABLE LEADER']['RTC DAY {TS}']
                    hour = ensemble['VARIABLE LEADER']['RTC HOUR {TS}']
                    minute = ensemble['VARIABLE LEADER']['RTC MINUTE {TS}']
                    second = ensemble['VARIABLE LEADER']['RTC SECOND {TS}']
                    hundredth = ensemble['VARIABLE LEADER']['RTC HUNDREDTHS {TS}']
                    try:
                        dtime = datetime.datetime(year,month,day,hour,minute,second,hundredth*1000) 
                    except: 
                        dtime = np.nan
                    return dtime
                        
                        
                        
        ef,el = self.__get_first_and_last_ensembles()
        self.metadata = metadata(self)
   
    
        import_file = kwargs.pop('import_file',True)
        print_progress = kwargs.pop('print_progress',True)
        #######################################################################
        
        if import_file:

            ## Read the file 
            start = kwargs.pop('start',1)
            end = kwargs.pop('end',self.metadata.n_ensembles_in_file)
            
            self._file = open(self._filepath,"rb")
            self.__read_ensembles(start,end, print_progress = print_progress)
            self._file.close()
            
            del self._file
            
            if print_progress:
                print(f'\rloaded {self._n_ensembles}/{self.metadata.n_ensembles_in_file} ensembles from {self.metadata.filepath.split(os.sep)[-1]}'.ljust(500), end = '\n')
            

                
        

    def __get_first_and_last_ensembles(self):
        #retrieve first and last ensembles
        self._file= open(self._filepath,"rb")

        self._file.seek(self.__find_next_ensemble())

        first_ensemble = self.__read_ensemble()
        self._file.seek(0,os.SEEK_END)
        self._file.seek(self.__find_previous_ensemble())
        last_ensemble = self.__read_ensemble()
        
        self._file.close()
        del self._file


        return first_ensemble,last_ensemble  
    
    
    def __skip_to_ensemble(self,n):
        
        
        
        # identify the ensemble in the file with number n
        def get_relative_ensemble_number():
            '''
            determine the ensemble number relative to the first ensemble in the 
            file. 1 = first ensemble in file. 
            assumes that the file is at the ensemble header byte position. 

            '''
 
            init_pos = self._file.tell()
            ens = self.__read_ensemble()
            self._file.seek(self._file.tell()+self._address_offsets[1])# move to variable leader start byte 
            en = ens['VARIABLE LEADER']['ENSEMBLE NUMBER'] - self.metadata.first_ensemble_in_file + 1
            self._file.seek(init_pos)
            return en


        init_pos = self._file.tell()
        init_guess = self.metadata.ensemble_size*max((n-1),0)
        
    
        
        self._file.seek(init_guess)

        self._file.seek(self.__find_next_ensemble())
        
        
        ## adjust for first ensemble in the file 
        
        en = get_relative_ensemble_number() 
        diff = en - n

        #search = False
        
        maxiter = self.metadata.n_ensembles_in_file
        _iter = 0
        success = True # successful search
        while diff!=0:
            _iter+=1
            #search = True
            if diff>0: 
                #print(diff)
                self._file.seek(self.__find_previous_ensemble(offset = True))
                #print(f'\rb {diff} en = {en}  n = {n}', end = '\r')
                #time.sleep(.1)
            elif diff<0: 
                #print(f'\rf {diff} en = {en} n = {n}', end = '\n')
                self._file.seek(self.__find_next_ensemble(offset = True))
                #time.sleep(.1)
                
                
            en = get_relative_ensemble_number()
            diff = en - n
            
            
            
            
            if _iter > maxiter:
                success = False # search failed
                break
          
         
        if success:
            self._file.seek(self.__find_previous_ensemble()) # adjust for last ensemble read
        else: # if search failed, return to initial file position 
            self._file.seek(init_pos)
            # if search failed, return to start point 
            
        # elif diff>0: self._file.seek(self.__find_next_ensemble(offset = True))
        # else: self._file.seek(self.__find_previous_ensemble())
            
        
        return success
        
        
        
        


    def __find_previous_ensemble(self,dist = 5000, maxiter = 100, offset = False):
        """
        find the position of the first byte of the previous valid ensemble in the 
        file. If no valid ensembles are found, then the position of the beginning of 
        the search file will be returned. 
        
        The file is always returned to its starting position at the time of the 
        function call. 

        Parameters
        ----------
        dist : int, optional
            number of bytes to read in each iteration. This value must be larger 
            than the size of an ensemble to The default is 2000.
        maxiter : int, optional
            numer of iterations to perform. The default is 100.
        offset : bool, optinal
            whether to ignore the first two bytes (case where its on the next ensemble already)

        Returns
        -------
        pos : int
            position of the starting byte for the next valid enseble in the file. 
            If no valid ensembles are found, then the position of the end of the file will be returned.
        """


        init_pos = self._file.tell() # file position at the beginning of the search 
        # start_pos = max(init_pos - dist,0) # starting position in file for the current iteration
        
        if not offset:start_pos = max(init_pos,0) # starting position in file for the current iteration
        else: start_pos = max(init_pos - 2,0) # starting position in file for the current iteration
        valid = False # indicator variable for successful search 
        _iter = 0 # number of iterations 
        while not valid: # while a valid ensemble has not been found,
            self._file.seek(start_pos) # seek to the start position for the iteration
            headers = [i for i in re.finditer(b'\x7f\x7f', self._file.read(dist), re.S)] # read bytes and search for an instance of the ensemble header ID b'\x7f\x7f'
            #print(headers)
            for header in np.flip(headers): # loop over identtified headers 
                pos = start_pos + header.start() # byte position for the beginning of the header 
                self._file.seek(pos)# seek to byte position for the beginning of the header 
                try: 
                    ensemble = self.__read_ensemble()
                    valid = self.__check_valid_ensemble(ensemble)
                    #print('p',ensemble['VARIABLE LEADER']['ENSEMBLE NUMBER'])
                except: valid = False
                if valid: break # break the loop if the ensemble is valid

            # step backwards
            start_pos = max(start_pos - dist,0)
            self._file.seek(start_pos)
            
            # update iteration count
            _iter+=1 
            
            ## other termination conditions
            term_conds = [_iter>=maxiter,
                          self._file.tell()== 0]
            
            
            
            if any(term_conds):
                pos = 0
                #print('maxout')
                break
        
            
        self._file.seek(init_pos) # return file to initial position 
        return pos 


    def __find_next_ensemble(self,dist = 5000, maxiter = 100,offset = False):
        """
        find the position of the first byte of the next valid ensemble in the 
        file. If no valid ensembles are found, then the position of the end of 
        the search file will be returned. 
        
        The file is always returned to its starting position at the time of the 
        function call. 

        Parameters
        ----------
        dist : int, optional
            number of bytes to read in each iteration. This value must be larger 
            than the size of an ensemble to The default is 3000.
        maxiter : int, optional
            numer of iterations to perform. The default is 100.
        offset : bool, optinal
            whether to ignore the first two bytes (case where its on the next ensemble already)

        Returns
        -------
        pos : int
            position of the starting byte for the next valid enseble in the file. 
            If no valid ensembles are found, then the position of the end of the file will be returned.
        """
        # global ensemble2
        # ensemble2 = self.__read_ensemble()
        init_pos = self._file.tell() # file position at the beginning of the search 
        if not offset:start_pos = max(init_pos,0) # starting position in file for the current iteration
        else: start_pos = max(init_pos + 2,0) # starting position in file for the current iteration
        valid = False # indicator variable for successful search 
        _iter = 0 # number of iterations 
        while not valid: # while a valid ensemble has not been found,
            self._file.seek(start_pos) # seek to the start position for the iteration
            headers = [i for i in re.finditer(b'\x7f\x7f', self._file.read(dist), re.S)] # read bytes and search for an instance of the ensemble header ID b'\x7f\x7f'
            for header in headers: # loop over identtified headers 
                pos = start_pos + header.start() # byte position for the beginning of the header 
                self._file.seek(pos)# seek to byte position for the beginning of the header
                
                # ensemble = self.__read_ensemble()
                # valid = self.__check_valid_ensemble(ensemble)
                #ensemble = self.__read_ensemble()
                try: 
 
                    ensemble = self.__read_ensemble()
                    valid = self.__check_valid_ensemble(ensemble)
                    #print(f'pos {pos}',ensemble['VARIABLE LEADER']['ENSEMBLE NUMBER'])
                    
                except: valid = False
                if valid: break # break the loop if the ensemble is valid

            # step backwards
            start_pos = start_pos + dist -1
            self._file.seek(start_pos)
            _iter+=1 # update iteration count 
            #print(start_pos)
            ## other termination conditions
            term_conds = [_iter>maxiter,
                          self._file.tell()>=os.path.getsize(self._filepath)]
        
            if any(term_conds):
                pos = os.path.getsize(self._filepath)
                #print(term_conds)
                break

        self._file.seek(init_pos) # return file to initial position 
        
        
       
        return pos 

    

    def __check_valid_ensemble(self,ensemble):
        """
        Check that an ensemble is valid 

        Parameters
        ----------
        ensemble : dict
            ensemble dictionary returned by __read_ensemble()

        Returns
        -------
        valid : bool
            True if all checks are passed
        """

        
        
        
        valid = True
        
        ## check ensemble header fields 
        if ensemble['ENSEMBLE HEADER']['N DATA TYPES']>10: valid = False     
        if ensemble['ENSEMBLE HEADER']['N DATA TYPES']<1: valid = False
        if ensemble['ENSEMBLE HEADER']['HEADER ID']!=127: valid = False     
        if ensemble['ENSEMBLE HEADER']['DATA SOURCE ID']!=127: valid = False 
        
        # check a random data field 
        if not any(ensemble['CORRELATION MAGNITUDE']): valid = False




        # try to parse the date
        century = str(ensemble['VARIABLE LEADER']['RTC CENTURY'])
        if not century in ['19','20']: century = '20' 
        year = int(century + str(ensemble['VARIABLE LEADER']['RTC YEAR {TS}']))
        month= ensemble['VARIABLE LEADER']['RTC MONTH {TS}']
        day = ensemble['VARIABLE LEADER']['RTC DAY {TS}']
        hour = ensemble['VARIABLE LEADER']['RTC HOUR {TS}']
        minute = ensemble['VARIABLE LEADER']['RTC MINUTE {TS}']
        second = ensemble['VARIABLE LEADER']['RTC SECOND {TS}']
        hundredth = ensemble['VARIABLE LEADER']['RTC HUNDREDTHS {TS}']
        
        try:
            datetime.datetime(year,month,day,hour,minute,second,hundredth*1000)
        except: 
            valid = False
        
        

            
        
        return valid
    
    
    
    def __read_ensembles(self,start = None,end = None,print_progress = True):
        """
        Read ensembles from the pd0 file. all ensembles between start and end
        will be read. 

        Parameters
        ----------
        start : int, optional
            first ensemble to read. If not specified, the first ensemble in the 
            file will be used. 
        end : int, optional
            last ensemble to read. If not specified, the last ensemble in the 
            file will be used. 
        print_progress : bool, optional
            If true a progress bar will be printed. The default is true.


        """
        

        ## set default parameters
        if start == None:
            start = 1 
        if end == None:
            end = self.metadata.n_ensembles_in_file 
        
        #print(start,end)
        ## check that start/end inputs are valid 
        message = f'Invalid start/end ensemble'
        if (start < 1) or (start >= self.metadata.n_ensembles_in_file ):
            raise ValueError(message)
        if (end <= 1) or (end > self.metadata.n_ensembles_in_file ):
            raise ValueError(message)
        if start>end:
            raise ValueError('start ensemble is greater than end ensemble')




    
        


        # # initalize the progress bar
        # if print_progress: ptools.printProgressBar(0, end-start,taskname = f'{self.metadata.filepath.split(os.sep)[-1]}', prefix = 'parsing .pd0')
        
        
        en = start # most recent ensemble number read 
        self._n_ensembles = 0 # number of ensembles read so far
        
        ## open the file for reading 
        self._file= open(self._filepath,"rb")
        self.__skip_to_ensemble(start) # skip to the start ensemble
        
        
        ## read the next ensemble until the end ensemble has been reached
        while en<=end:    
            valid = False # indicator for whther the read was successful
            #print(en)
            try:
                ensemble = self.__read_ensemble()
                valid = self.__check_valid_ensemble(ensemble) # check if it is a valid ensemble 
            except: 
                None
 


            if valid:# if its a valid ensemble update some other stuff
                # account for ensemble rollover
                self.ensemble_data.append(ensemble) # append to global ensemble data
                self._n_ensembles +=1 # update ensemble number counter 
                if print_progress: ptools.printProgressBar(self._n_ensembles-1, end-start,taskname = f'{self.metadata.filepath.split(os.sep)[-1]}', prefix = 'parsing .pd0')## print progress
                en += 1 #ensemble['VARIABLE LEADER']['ENSEMBLE NUMBER'] # update the ensemble number 
                #print(en)
                
            else: # if ensemble is not valid, skip to the next valid ensemble 
            
                if (self.metadata.filesize -self._file.tell())<self.metadata.ensemble_size:
                    self._file.close()
                    break
                else:
                    ## check if we're close to the end of the file 
                    curr_pos = self._file.tell()
                    success = self.__skip_to_ensemble(self._n_ensembles+start) # skip to last known ensemble 
                    self._file.seek(self.__find_next_ensemble(offset = False)) # move forward one ensemble
                
                
                # print(self._n_ensembles+start+1)
                #success = self.__skip_to_ensemble(self._n_ensembles+start+1)
                
                
                # if not success:
                #     print('skipping')
                #     self._file.seek(self.__find_next_ensemble(offset = True))

                

        self.metadata.first_ensemble_read = self.ensemble_data[0]['VARIABLE LEADER']['ENSEMBLE NUMBER']
        self.metadata.last_ensemble_read  = self.ensemble_data[-1]['VARIABLE LEADER']['ENSEMBLE NUMBER'] 
        
        
        
    def __read_ensemble(self):
        ## check if the file is open
        ensemble_start_byte = self._file.tell()
        
        self._checksum = [] #add new entry to the file checksum
        
        ensemble = { 'ENSEMBLE HEADER':{},
                      'FIXED LEADER': {},
                      'VARIABLE LEADER': {},
                      'VELOCITY': [],
                      'CORRELATION MAGNITUDE':[],
                      'ECHO INTENSITY':[],
                      'PERCENT GOOD':[],
                      'BOTTOM TRACK':[],
                      'SYSTEM CONFIGURATION':{},
                      'COORDINATE SYSTEM': {}} 

        ensemble['ENSEMBLE HEADER'] = self.__read_ensemble_header()
        self._file.seek(ensemble_start_byte+self._address_offsets[0])
        ensemble['FIXED LEADER'] = self.__read_fixed_leader()
        self._file.seek(ensemble_start_byte+self._address_offsets[1])
        ensemble['VARIABLE LEADER'] = self.__read_variable_leader()
        
        

        
    
        self._file.seek(ensemble_start_byte+self._address_offsets[2])
        ensemble['ENSEMBLE HEADER']['VELOCITY ID'] = self.__read_next_bytes(data_ID_code_format)#_NextLittleEndianUnsignedShort(file,2,decode = True)
        velocity_data = []
        for cell in range(ensemble['FIXED LEADER']['NUMBER OF CELLS {WN}']):
            cell_data = []
            for beam in range(4):#ensemble['FIXED LEADER']['NUMBER OF BEAMS']):
                cell_data.append(self.__read_next_bytes(velocity_format))
            velocity_data.append(cell_data) 

        ## Parse data type 4 (correlation Magnitude)
        ensemble['ENSEMBLE HEADER']['ID CODE 4'] =self.__read_next_bytes(data_ID_code_format)# _NextLittleEndianUnsignedShort(file,2, decode = True)
        corr_mag_data = []
        
        for cell in range(ensemble['FIXED LEADER']['NUMBER OF CELLS {WN}']):
            cell_data = []
            for beam in range(4):#ensemble['FIXED LEADER']['NUMBER OF BEAMS']):
                cell_data.append(self.__read_next_bytes(coor_mag_format)) #_NextLittleEndianUnsignedShort(file,1,decode = field[3]))
            corr_mag_data.append(cell_data)

            
        ## Parse data type 5 (echo intensity)
        ensemble['ENSEMBLE HEADER']['ID CODE 5'] =self.__read_next_bytes(data_ID_code_format)# _NextLittleEndianUnsignedShort(file,2,decode = True)
        echo_intensity_data = []
        
        for cell in range(ensemble['FIXED LEADER']['NUMBER OF CELLS {WN}']):
            cell_data = []
            for beam in range(4):#ensemble['FIXED LEADER']['NUMBER OF BEAMS']):
                cell_data.append(self.__read_next_bytes(echo_intensity_format))#_NextLittleEndianUnsignedShort(file,1,decode = field[3]))
            echo_intensity_data.append(cell_data)    
         
        ## Parse data type 6 (percent good)
        ensemble['ENSEMBLE HEADER']['ID CODE 6'] = self.__read_next_bytes(data_ID_code_format)#_NextLittleEndianUnsignedShort(file,2, decode = True)
        pct_good_data = []
        
        for cell in range(ensemble['FIXED LEADER']['NUMBER OF CELLS {WN}']):
            cell_data = []
            for beam in range(4):#ensemble['FIXED LEADER']['NUMBER OF BEAMS']):
                cell_data.append(self.__read_next_bytes(pct_good_format))#_NextLittleEndianUnsignedShort(file,1,decode = field[3]))
            pct_good_data.append(cell_data)      
           
        # read bottom track data, if recorded
        if ensemble['ENSEMBLE HEADER']['N DATA TYPES'] ==7:
            bottom_track = {}
            for field in bottom_track_format:  
                bottom_track[field[0]] = self.__read_next_bytes(field)# _NextLittleEndianUnsignedShort(file,field[1],decode = field[3]) 
        else: bottom_track = None          
        

        ensemble['VELOCITY'] = velocity_data
        ensemble['CORRELATION MAGNITUDE']= corr_mag_data
        ensemble['ECHO INTENSITY']=echo_intensity_data
        ensemble['PERCENT GOOD']=pct_good_data
        ensemble['BOTTOM TRACK']=bottom_track
   
        
        
        #read reserved bit data 
        ensemble['ENSEMBLE HEADER']['RESERVED BIT DATA'] = self.__read_next_bytes(data_ID_code_format)#_NextLittleEndianUnsignedShort(file,2,decode = True)
       
        # read end of ensemble checksum 
        file_checksum = struct.unpack('<H',self._file.read(2))[0] #chacksum to verify

        
        
        passed_checksum = True
        diff = sum(bytearray(b''.join(self._checksum)))%65536 - file_checksum
        if diff != 0:
            #print(f'checksum failed reading ensemble {ensemble["VARIABLE LEADER"]["ENSEMBLE NUMBER"]} \n {diff} byte discrepancy')
            passed_checksum = False
            
           
           
        ## get system configuration parameters 
        try:
            system_configuration = self.__parse_system_configuration(ensemble['FIXED LEADER']['SYSTEM CONFIGURATION'])  
        except: 
            system_configuration = None
           
        coord_sys = self.__parse_EX_command(ensemble['FIXED LEADER']['COORDINATE TRANSFORM {EX}'])
        

        ensemble['SYSTEM CONFIGURATION']=system_configuration
        ensemble['COORDINATE SYSTEM']=coord_sys
        
        return ensemble
        
    def __read_ensemble_header(self):
        #assumes file is already in starting position 
        ensemble_header = {}
        #self.__skip_to_next_header()
        for field in ensemble_header_format:
            ensemble_header[field[0]] = self.__read_next_bytes(field)
           
        ensemble_header['N DATA TYPES'] = max(ensemble_header['N DATA TYPES'],6)    
            
        ensemble_header['ADDRESS OFFSETS'] = []
        for n in range(ensemble_header['N DATA TYPES']):
            ensemble_header['ADDRESS OFFSETS'].append(self.__read_next_bytes(address_offsets_format))
        self._address_offsets = ensemble_header['ADDRESS OFFSETS']

        return ensemble_header
    
    def __read_fixed_leader(self):
        #assumes file is already in starting position 
        fixed_leader = {}
        for field in fixed_leader_format:
            fixed_leader[field[0]] = self.__read_next_bytes(field)
        return fixed_leader
    
    def __read_variable_leader(self):  
        #assumes file is already in starting position
        variable_leader = {}
        for field in variable_leader_format:
                variable_leader[field[0]] = self.__read_next_bytes(field)
                
                
        # ## adjust for ensemble rollover 
        rollover = variable_leader['ENSEMBLE # MSB']
        variable_leader['ENSEMBLE NUMBER'] += rollover*65535


        return variable_leader 
            

                     
    def __read_next_bytes(self,fmt):
        decode = fmt[4]
        raw_bytes = self._file.read(fmt[1])
        # n_bytes_read += n
        self._checksum.append(raw_bytes)
        
        if fmt[1] > 1:
            if fmt[3] =='B':
                fmtstr = f'{fmt[2]}{fmt[1]}{fmt[3]}' 
                
            elif fmt[3] in ['Q','I']:
                fmtstr = f'{fmt[2]}{fmt[3]}' 
                
            else:
                fmtstr = f'{fmt[2]}{int(fmt[1]/2)}{fmt[3]}'
                
            out = struct.unpack(fmtstr,raw_bytes)
        else:
            out = raw_bytes
            
        if decode:    
            return out[0]
        else:
            return raw_bytes
        
        
    def __get_LE_bit_string(self,byte): 
        """
        make a bit string from little endian byte
        
        Args:
            byte: a byte
        Returns:
            a string of ones and zeros, the bits in the byte
        """
        # surely there's a better way to do this!!
        bits = ""
        for i in [7, 6, 5, 4, 3, 2, 1, 0]:  # Little Endian
            if (byte >> i) & 1:
                bits += "1"
            else:
                bits += "0"
        return bits     
    
          
    def __parse_system_configuration(self,syscfg):
        """
        determine the system configuration parameters from 2-byte hex
        
        Args:
            syscfg: 2-byte hex string 
        Returns:
            dictionary of system configuration parameters
        """    
    
        LSB = self.__get_LE_bit_string(syscfg[0])
        MSB = self.__get_LE_bit_string(syscfg[1])
        
        ## determine system configuration
        #key for Beam facing
        beam_facing = {'0':'DOWN',
                    '1':'UP'}
        
        #key for XDCR attached
        xdcr_att = {'0':'NOT ATTACHED',
                    '1':'ATTACHED'}
        
        # key for sensor configuration
        sensor_cfg = {'00':'#1',
                      '01':'#2',
                      '10':'#3'}
        
        # key for beam pattern
        beam_pat = {'0':'CONCAVE',
                    '1':'CONVEX'}
        
        # key for system frequencies
        sys_freq = {'000':'75-kHz',
                    '001':'150-kHz',
                    '010':'300-kHz',
                    '011':'600-kHz',
                    '100':'1200-kHz',
                    '101':'2400-kHz',} 
        
        ## determine system configuration from MSB
        janus = {'0100':'4-BM',
                '0101': '5-BM (DEMOD)',
                '1111': '5-BM (2 DEMD)'}
        
        beam_angle = {'00': '15E',
                     '01': '20E',
                     '10': '30E',
                     '11': 'OTHER'}
        
        system_configuration = {}
        system_configuration['BEAM FACING']  = beam_facing[LSB[0]]
        system_configuration['XDCR HD']      = xdcr_att[LSB[1]]
        system_configuration['SENSOR CONFIG']= sensor_cfg[LSB[2:4]]
        system_configuration['BEAM PATTERN'] = beam_pat[LSB[4]]
        system_configuration['FREQUENCY']    = sys_freq[LSB[5:]]
        try:
            system_configuration['JANUS CONFIG'] = janus[MSB[:4]]
        except: system_configuration['JANUS CONFIG'] = 'UNKNOWN'
        
        system_configuration['BEAM ANGLE']   = beam_angle[MSB[-2:]]
    
        return system_configuration   
    
    
    def __parse_EX_command(self,ex):
        """
        determine the coordinate transformation processing parameters (EX command). parameters from 1-byte hex
        
        Args:
            ex: 1-byte hex string 
        Returns:
            string - coordinate transformation processing parameter 
        """      
    
        LSB = self.__get_LE_bit_string(ex[0])
        
        coord_sys = {'00': 'BEAM COORDINATES',
                     '01': 'INSTRUMENT COORDINATES',
                     '10': 'SHIP COORDINATES',
                     '11': 'EARTH COORDINATES'}    
        
        coord_system= coord_sys[LSB[3:5]]
        
        return coord_system

 
    
    def write_pd0(self,fname):
        self._file= open(f'{fname}.000','wb')  
    # __write_next_bytes(127,ensemble_header_format[0],file)

        for e,ensemble in enumerate(self.ensemble_data):
            self.__write_ensemble(ensemble)
        self._file.close()   




    def __write_ensemble(self,ensemble): 
        self._checksum = bytearray(0)
        
        # # write the ensemble header 
        for field in ensemble_header_format:
            self.__write_next_bytes(ensemble['ENSEMBLE HEADER'][field[0]],field)
            
        for n in range(ensemble['ENSEMBLE HEADER']['N DATA TYPES']):
            self.__write_next_bytes(ensemble['ENSEMBLE HEADER']['ADDRESS OFFSETS'][n],address_offsets_format)
        
            
        #Write the fixed leader (data type 1)
        for field in fixed_leader_format:
            self.__write_next_bytes(ensemble['FIXED LEADER'][field[0]],field)
            
        for field in variable_leader_format:
            self.__write_next_bytes(ensemble['VARIABLE LEADER'][field[0]],field)
               
        ## Write data type 3 (velocity)
        self.__write_next_bytes(ensemble['ENSEMBLE HEADER']['VELOCITY ID'],data_ID_code_format)
        for cell in range(ensemble['FIXED LEADER']['NUMBER OF CELLS {WN}']):
            cell_data = []
            for beam in range(ensemble['FIXED LEADER']['NUMBER OF BEAMS']):
                self.__write_next_bytes(ensemble['VELOCITY'][cell][beam],velocity_format)
        
        ## Write data type 4 (correlation Magnitude)
        self.__write_next_bytes(ensemble['ENSEMBLE HEADER']['ID CODE 4'],data_ID_code_format)
        for cell in range(ensemble['FIXED LEADER']['NUMBER OF CELLS {WN}']):
            cell_data = []
            for beam in range(ensemble['FIXED LEADER']['NUMBER OF BEAMS']):
                self.__write_next_bytes(ensemble['CORRELATION MAGNITUDE'][cell][beam],coor_mag_format)
                
        ## Write data type 5 (echo intensity)
        self.__write_next_bytes(ensemble['ENSEMBLE HEADER']['ID CODE 5'],data_ID_code_format)
        for cell in range(ensemble['FIXED LEADER']['NUMBER OF CELLS {WN}']):
            cell_data = []
            for beam in range(ensemble['FIXED LEADER']['NUMBER OF BEAMS']):
                self.__write_next_bytes(ensemble['ECHO INTENSITY'][cell][beam],echo_intensity_format)
        
        ## Write data type 6 (percent good)
        self.__write_next_bytes(ensemble['ENSEMBLE HEADER']['ID CODE 6'],data_ID_code_format)
        for cell in range(ensemble['FIXED LEADER']['NUMBER OF CELLS {WN}']):
            cell_data = []
            for beam in range(ensemble['FIXED LEADER']['NUMBER OF BEAMS']):
                self.__write_next_bytes(ensemble['PERCENT GOOD'][cell][beam],pct_good_format)     
          
        # write bottom track data, if recorded
        if ensemble['BOTTOM TRACK']:
            if ensemble['ENSEMBLE HEADER']['N DATA TYPES'] ==7:
                for field in bottom_track_format:  
                    self.__write_next_bytes(ensemble['BOTTOM TRACK'][field[0]],field) 
            
        
        #write reserved bit data 
        self.__write_next_bytes(ensemble['ENSEMBLE HEADER']['RESERVED BIT DATA'],data_ID_code_format)
        
        # write end of ensemble checksum 
        self.__write_next_bytes(sum(self._checksum)%65536,data_ID_code_format) #chacksum to verify
        
    
    
    def __write_next_bytes(self,x,fmt):
        decoded = fmt[4]
        if decoded:   
            if fmt[3] == 'h':
                write_bytes = x.to_bytes(fmt[1], byteorder='little',signed = True)
            else:
                write_bytes = x.to_bytes(fmt[1], byteorder='little',signed = False)
        else:
            write_bytes = x
            
        # n_bytes_written += n    
        self._checksum += bytearray(write_bytes)  
        self._file.write(write_bytes)   
        
###############################################################################
#%% Analytics Wrapper 

class DataSet(Pd0):
    """
    Extends the Pd0 class to provide enhanced analytical capabilities specifically
    tailored for handling and analyzing ADCP data.

    This class offers methods for extracting time series data from variable and fixed
    leaders, computing derived quantities like velocities and displacements, and applying
    corrections such as timezone or magnetic deviations. It also facilitates the integration
    with other data types like PT3 data for comprehensive analyses.

    Attributes:
        timezone_correction (int): Hours to adjust the time data for local timezone corrections.
        magnetic_deviation_correction (float): Degrees to adjust the velocity data for magnetic deviations.
        name (str): A derived name from the filepath, generally the filename.
        n_ensembles (int): Number of ensembles loaded into memory.
        config (config_parameters): Configuration parameters derived from the ADCP data.
        plot (plotting): A plotting tool associated with the dataset for visual analysis.
        processing (processing): Processing tools for data manipulation and computation.
        geometry (geometry): Geometrical tools for handling spatial dimensions and transformations.
        mask (masking): Masking tools for data cleaning and preparation.
        PT3 (PT3, optional): PT3 data associated with the dataset, if provided.

    Methods:
        __init__(filepath, **kwargs): Initializes the DataSet instance with the specified ADCP data file and optional parameters.
        get_ensemble_datetimes(): Returns an array of datetime objects representing the timestamps of each ensemble.
        get_leader_data(field, leader='VARIABLE LEADER', dtype=int): Retrieves time series data for a specified field from the leader data.
        get_ensemble_numbers(): Returns an array of ensemble numbers.
        get_sensor_transmit_pulse_lengths(): Retrieves the ADCP transmit pulse lengths.
        get_sensor_temperature(): Retrieves the temperature data from the sensor.
        get_bit_result(): Retrieves the built-in test result from the ADCP.
        get_salinity(): Retrieves the salinity data from the sensor.
        get_sensor_pitch(): Retrieves the pitch data from the sensor.
        get_sensor_roll(): Retrieves the roll data from the sensor.
        get_sensor_heading(): Retrieves the heading data from the sensor.
        get_sensor_transducer_depth(): Retrieves the depth of the transducer below the water surface.
        get_velocity(field_name='VELOCITY'): Retrieves velocity data along with calculated displacements.
        get_bottom_track(): Retrieves bottom tracking data from the ADCP.
        get_ensemble_array(field_name='ECHO INTENSITY', mask=True): Formats specified ensemble data field into a numpy array with optional masking.
    """
    
    def __init__(self,filepath,**kwargs):
        super().__init__(filepath,**kwargs)
        
        
        # parse kwargs
        self.timezone_correction = kwargs.pop('timezone_correction',0)
        self.magnetic_deviation_correction = kwargs.pop('magnetic_deviation_correction',0)  

        self.name = filepath.split(os.sep)[-1]
            
        self.n_ensembles = len(self.ensemble_data)
        #self.set_instrument_config_parameters() # set instrument configuration params
        


        self.config = config_parameters(self)
        self.plot = plotting(self)        
        self.processing = processing(self)
        self.geometry = geometry(self)
        self.mask = masking(self)
        
        
                    
        if kwargs.get('pt3_filepath'):
            self.PT3 = PT3(kwargs.get('pt3_filepath'))

    

    def get_ensemble_datetimes(self,ensemble = None):
        """
        Generate numpy array of datetimes for ensembles. 
        Args:
            None
        Returns:
            numpy array with dimensions (n_ensembles)  
        """           

        dtimes =[]
        for e,ensemble in enumerate(self.ensemble_data):
            century = str(ensemble['VARIABLE LEADER']['RTC CENTURY'])
            if not century in ['19','20']: century = '20' 
            year = int(century + str(ensemble['VARIABLE LEADER']['RTC YEAR {TS}']))
            month= ensemble['VARIABLE LEADER']['RTC MONTH {TS}']
            day = ensemble['VARIABLE LEADER']['RTC DAY {TS}']
            hour = ensemble['VARIABLE LEADER']['RTC HOUR {TS}']
            minute = ensemble['VARIABLE LEADER']['RTC MINUTE {TS}']
            second = ensemble['VARIABLE LEADER']['RTC SECOND {TS}']
            hundredth = ensemble['VARIABLE LEADER']['RTC HUNDREDTHS {TS}']
            try:
                dtimes.append(datetime.datetime(year,month,day,hour,minute,second,hundredth*1000) + datetime.timedelta(hours = self.timezone_correction)) 
            except: 
                print(ensemble['VARIABLE LEADER']['RTC MONTH {TS}'])
                #print(str(ensemble['VARIABLE LEADER']['RTC YEAR {TS}']))
                dtimes.append(datetime.datetime(year,month,day,hour,minute,second,hundredth*1000) + datetime.timedelta(hours = self.timezone_correction)) 
                # dtimes.append(np.nan)
                # break
            
        dtimes = np.array(dtimes)
        return dtimes    


        
    
    def get_leader_data(self,field,leader = 'VARIABLE LEADER', dtype = int):
        
        """
        Get a timeseries of data from fixed leader or variable leader. field 
        names are identical to those in Workhorse Commands and Output Data 
        Format.

        Parameters
        ----------
        field : str
            field name.
        leader : ste, optional
            'FIXED LEADER' or 'VARIABLE LEADER'. The default is 'VARIABLE LEADER'.
        dtype : numpy dtype, optional
            data type for the output numpy array. The default is int.

        Returns
        -------
        data : numpy array
             One value for each ensemble.

        """
        
        data = np.empty(self.n_ensembles, dtype = int)
        for c,ensemble in enumerate(self.ensemble_data):
            data[c] = ensemble[leader][field]
        
        return data 
        
    def get_ensemble_numbers(self):
        """
        Get the ensemble number for every ensemble. 

        Returns
        -------
        ensemble_numbers : numpy array
            ensemble numbers. One value for each ensemble.
            
        """
        ensemble_numbers = self.get_leader_data(field = 'ENSEMBLE NUMBER',leader = 'VARIABLE LEADER')
        return ensemble_numbers

        
    def get_sensor_transmit_pulse_lengths(self):
        """
        Get ADCP transmit pulse lengths. Data is from the ensemble variable headers.

        Returns
        -------
        transmit_pulse_lengths : numpy array
            ADCP transmit pule lengths. One value for each ensemble.

        """
        
        transmit_pulse_lengths = self.get_leader_data(field = 'XMIT PULSE LENGTH BASED ON {WT}',leader = 'FIXED LEADER')/100
        return transmit_pulse_lengths  
    
    def get_sensor_temperature(self):
        """
        Temperature of the water at the transducer head
        (ET-command). This value may be a manual setting or a
        reading from a temperature sensor.
        Scaling: LSD = 0.01 degree; Range = -5.00 to +40.00 degrees
        
        Returns
        -------
        temperature : numpy array
            ADCP temperature data in degrees C. One value for each ensemble.

        """
        temperature = np.empty(self.n_ensembles)
        
        for c,ensemble in enumerate(self.ensemble_data):
            temperature[c] = ensemble['VARIABLE LEADER']['TEMPERATURE {ET}']/100
        return temperature
    
    def get_bit_result(self):
        """
        This field contains the results of the WorkHorse ADCP’s Builtin
        Test function. A zero code indicates a successful BIT
        result.
        
        Returns
        -------
        bit_result : numpy array
            ADCP bit result data. One value for each ensemble.

        """
        bit_result = np.empty(self.n_ensembles)
        
        for c,ensemble in enumerate(self.ensemble_data):
            bit_result[c] = ensemble['VARIABLE LEADER']['BIT RESULT']/100
        return bit_result
    
    def get_salinity(self):
        """
        Salinity value of the water at the transducer
        head (ES-command). This value may be a manual setting or
        a reading from a conductivity sensor.
        Scaling: LSD = 1 part per thousand; Range = 0 to 40 ppt
        
        Returns
        -------
        salinity : numpy array
            One value for each ensemble.

        """
        salinity = np.empty(self.n_ensembles)
        
        for c,ensemble in enumerate(self.ensemble_data):
            salinity[c] = ensemble['VARIABLE LEADER']['SALINITY {ES}']
        return salinity
    
    def get_sensor_pitch(self):
        """
        WorkHorse ADCP pitch angle (EP-command).
        This value may be a manual setting or a reading from a tilt
        sensor. Positive values mean that Beam #3 is spatially
        higher than Beam #4.
        Scaling: LSD = 0.01 degree; Range = -20.00 to +20.00 degrees
        Returns
        -------
        pitch : numpy array
            One value for each ensemble.

        """
        pitch = np.empty(self.n_ensembles)
        for c,ensemble in enumerate(self.ensemble_data):
            pitch[c] = ensemble['VARIABLE LEADER']['PITCH TILT 1 {EP}']/100
        return pitch
    
    def get_sensor_roll(self):
        """
        WorkHorse ADCP roll angle (ER-command).
        This value may be a manual setting or a reading from a tilt
        sensor. For up-facing WorkHorse ADCPs, positive values
        mean that Beam #2 is spatially higher than Beam #1. For
        down-facing WorkHorse ADCPs, positive values mean that
        Beam #1 is spatially higher than Beam #2.
        Scaling: LSD = 0.01 degree; Range = -20.00 to +20.00 degrees

        Returns
        -------
        roll : numpy array
            One value for each ensemble.

        """
        roll = np.empty(self.n_ensembles)
        for c,ensemble in enumerate(self.ensemble_data):
            roll[c] = ensemble['VARIABLE LEADER']['ROLL TILT 2 {ER}']/100
        return roll
    
    def get_sensor_heading(self):
        """
        WorkHorse ADCP heading angle (EHcommand).
        This value may be a manual setting or a reading
        from a heading sensor.
        Scaling: LSD = 0.01 degree; Range = 000.00 to 359.99 degrees
        
        Returns
        -------
        heading : numpy array
             One value for each ensemble.

        """

        heading = np.empty(self.n_ensembles)
        for c,ensemble in enumerate(self.ensemble_data):
            heading[c] = ensemble['VARIABLE LEADER']['HEADING {EH}']/100
        return heading
    
    def get_sensor_transducer_depth(self):
        """
        Depth of the transducer below the water surface
        (ED-command). This value may be a manual setting or a
        reading from a depth sensor.
        Scaling: LSD = 1 decimeter; Range = 1 to 9999 decimeters
        
        Returns
        -------
        transducer_depth : numpy array
             One value for each ensemble.

        """

        transducer_depth = np.empty(self.n_ensembles)
        for c,ensemble in enumerate(self.ensemble_data):
            transducer_depth[c] = ensemble['VARIABLE LEADER']['DEPTH OF TRANSDUCER {ED}']
        

        return transducer_depth
    
    def get_velocity(self,field_name = 'VELOCITY'):

        """
        Retrieve velocity vectors including progressive vectors in m/s.
        Magnetic deviation correction is applied here. 
        Parameters
        -------
        field_name: str, optional
            ensemble field name to use for velocity data. 'VELOCITY' is default. 
            Other options might be 'VELOCITY CORRECTED' or other user specified velocity-like fields
        Returns
        -------
        u : numpy array
            u velocity array with dimensions (n_bins, n_ensembles)
        v : numpy array
            v velocity array with dimensions (n_bins, n_ensembles)
        z : numpy array
            z velocity array with dimensions (n_bins, n_ensembles)
        du : numpy array
            displacement in u direction. Array with dimensions (n_bins, n_ensembles)
        dv : numpy array
            displacement in v direction. Array with dimensions (n_bins, n_ensembles)
        dz : numpy array
            displacement in z direction. Array with dimensions (n_bins, n_ensembles)
        err: numpy array
            error velocity array with dimensions (n_bins, n_ensembles)
    
        """
        

        
        
        u = np.empty((self.n_ensembles,self.config.number_of_cells))
        v = np.empty((self.n_ensembles,self.config.number_of_cells))
        z = np.empty((self.n_ensembles,self.config.number_of_cells))
        ev = np.empty((self.n_ensembles,self.config.number_of_cells))
        for e,ensemble in enumerate(self.ensemble_data):
            # cast velocity data as float
            vel_data = np.array(ensemble[field_name]).astype('float')
            # mark nan values 
            vel_data[vel_data==-32768] = np.nan
            vel_data[vel_data==32768] = np.nan
            
            # convert to m/s
            vel_data = vel_data*.001


            if len(vel_data) == self.config.number_of_cells:
                u[e,:] = vel_data[:,0]
                v[e,:] = vel_data[:,1]
                z[e,:] = vel_data[:,2]
                ev[e,:] = vel_data[:,3]
            else:
                u[e,:] = np.nan
                v[e,:] = np.nan
                z[e,:] = np.nan
                ev[e,:] = np.nan
            

        if self.magnetic_deviation_correction!=0:
            for b in range(self.config.number_of_cells): # loop over all bins and calculate rotated velocites for each
                X = np.array([u[:,b],v[:,b]])
                
                X_rot = ptools.gen_rot_z(self.magnetic_deviation_correction)[:2,:2]
                #print(X_rot.shape,X.shape)
                X_rot = np.dot(X_rot,X)
                # update u and v
                u[:,b] = X_rot[0,:]
                v[:,b] = X_rot[1,:]    
                
        ## gen prog vector components 
        t = self.get_ensemble_datetimes()
        to_sec = np.vectorize(lambda x: x.seconds) # vectorized function to convert datetime delta to total seconds
        dt = np.empty(self.n_ensembles)
        dt[:-1] = to_sec(np.diff(t))
        dt[-1] = dt[-2] #assign last value
        dt = np.outer(dt,np.ones(self.config.number_of_cells))
        du = u*dt
        dv = v*dt
        dz = z*dt
        
        #transpose to correct dimensions and apply active masks 
        # u = self.mask.apply_masks(u.T)
        # v = self.mask.apply_masks(v.T)
        # z = self.mask.apply_masks(z.T)
        # du = self.mask.apply_masks(du.T)
        # dv = self.mask.apply_masks(dv.T)
        # dz = self.mask.apply_masks(dz.T)
        # ev = self.mask.apply_masks(ev.T)
        
        return u,v,z,du,dv,dz,ev     

    def get_bottom_track(self):
        """
        

        Parameters
        ----------
        beam_number : int
            beam number to use. if zero the beam average will be returned.

        Returns
        -------
        bt_range : numpy array
            numpy array of distance to bottom 

        """
        #
        bt_range = np.empty((4,self.n_ensembles))
        for e in range(self.n_ensembles):
            if self.ensemble_data[e]['BOTTOM TRACK']:
                for b in range(self.config.number_of_beams):
                    bt_range[b,e] = self.ensemble_data[e]['BOTTOM TRACK'][f'BEAM#{b+1} BT RANGE']/100
            else: bt_range[:,e] = np.nan
        return bt_range 
    
        #else: print('No Bottom Track Data')
        
        #raise NotImplementedError()


    def get_ensemble_array(self,field_name = 'ECHO INTENSITY', mask = True):
        f"""
        Format ensemble data field into a numpy array. All active masks are applied 
        to the ensemble data. 
    
        Parameters
        ----------
        field_name : str, optional
            Ensemble data type (excluding velocity). ['ECHO INTENSITY',
            'PERCENT GOOD','CORRELATION MAGNITUDE', 'SIGNAL TO NOISE RATIO',
            'ABSOLUTE BACKSCATTER'). The default is 'ECHO INTENSITY'.
        mask : bool, optional 
            If True, all activated masks will be applied to the ensemble array.
            if False, the raw data will be returned. 
    
        Returns
        -------
        X : numpy array
            Array of ensemble data with dimensions (n_beams,n_bins,n_ensembles).
    
        """
        ## Case where all beams are returned 
        X = np.empty((4,self.config.number_of_cells,self.n_ensembles))
        for c,ensemble in enumerate(self.ensemble_data):
            column_data = [i for i in ensemble[field_name]]
            X[:,:,c] = np.transpose(ensemble[field_name])
        
        
        X[abs(X)==32768] = np.nan
        # # apply any masks    
        if mask:
            X = self.mask.apply_masks(X)
        
        return X               
         



############### Misc Functions ################################################
       
 

############### Misc Functions ################################################


############### Masking Functions #############################################        

#%%
class config_parameters:
    def __init__(self,pd0,en = 0):
        self.n_ensembles = len(pd0.ensemble_data)
        self.number_of_beams = pd0.ensemble_data[en]['FIXED LEADER']['NUMBER OF BEAMS']
        self.beam_angle = pd0.ensemble_data[en]['FIXED LEADER']['BEAM ANGLE']
        self.bin_1_distance =pd0.ensemble_data[en]['FIXED LEADER']['BIN 1 DISTANCE']
        
        self.frequency      = pd0.ensemble_data[en]['SYSTEM CONFIGURATION']['FREQUENCY']
        self.beam_facing    = pd0.ensemble_data[en]['SYSTEM CONFIGURATION']['BEAM FACING']
        self.janus_config   = pd0.ensemble_data[en]['SYSTEM CONFIGURATION']['JANUS CONFIG']
        
        self.cpu_board_serial_number=pd0.ensemble_data[en]['FIXED LEADER']['CPU BOARD SERIAL NUMBER']
        self.cpu_fw_rev =pd0.ensemble_data[en]['FIXED LEADER']['CPU F/W REV.']
        self.cpu_fw_ver =pd0.ensemble_data[en]['FIXED LEADER']['CPU F/W VER.']
        self.instrument_serial_number =pd0.ensemble_data[en]['FIXED LEADER']['INSTRUMENT SERIAL NUMBER']
        self.lag_length =pd0.ensemble_data[en]['FIXED LEADER']['LAG LENGTH']
        self.no_code_reps =pd0.ensemble_data[en]['FIXED LEADER']['NO. CODE REPS']
        self.real_sim_flag =pd0.ensemble_data[en]['FIXED LEADER']['REAL/SIM FLAG']
        self.sensors_available =pd0.ensemble_data[en]['FIXED LEADER']['SENSORS AVAILABLE']
        self.system_configuration = pd0.ensemble_data[en]['FIXED LEADER']['SYSTEM CONFIGURATION']
        self.tpp_minutes =pd0.ensemble_data[en]['FIXED LEADER']['TPP MINUTES']
        self.tpp_seconds =pd0.ensemble_data[en]['FIXED LEADER']['TPP SECONDS']
        self.transmit_lag_distance =pd0.ensemble_data[en]['FIXED LEADER']['TRANSMIT LAG DISTANCE']
        
        self.pct_gd_minimum =pd0.ensemble_data[en]['FIXED LEADER']['%GD MINIMUM {WG}']
        self.blank_after_transmit =pd0.ensemble_data[en]['FIXED LEADER']['BLANK AFTER TRANSMIT {WF}']
        self.coordinate_transform =pd0.ensemble_data[en]['FIXED LEADER']['COORDINATE TRANSFORM {EX}']
        self.depth_cell_length =pd0.ensemble_data[en]['FIXED LEADER']['DEPTH CELL LENGTH {WS}'] #/100
        self.error_velocity_maximum =pd0.ensemble_data[en]['FIXED LEADER']['ERROR VELOCITY MAXIMUM {WE}']
        self.false_target_thresh =pd0.ensemble_data[en]['FIXED LEADER']['FALSE TARGET THRESH {WA}']
        self.heading_alignment =pd0.ensemble_data[en]['FIXED LEADER']['HEADING ALIGNMENT {EA}']
        self.heading_bias =pd0.ensemble_data[en]['FIXED LEADER']['HEADING BIAS {EB}']
        self.low_corr_thresh =pd0.ensemble_data[en]['FIXED LEADER']['LOW CORR THRESH {WC}']
        self.number_of_cells =pd0.ensemble_data[en]['FIXED LEADER']['NUMBER OF CELLS {WN}']
        self.pings_per_ensemble =pd0.ensemble_data[en]['FIXED LEADER']['PINGS PER ENSEMBLE {WP}']
        self.profiling_mode =pd0.ensemble_data[en]['FIXED LEADER']['PROFILING MODE {WM}']
        self.sensor_source =pd0.ensemble_data[en]['FIXED LEADER']['SENSOR SOURCE {EZ}']
        self.starting_cell_wp_ref =pd0.ensemble_data[en]['FIXED LEADER']['starting cell WP REF LAYER AVERAGE {WL} ending cell']
        self.system_bandwidth = pd0.ensemble_data[en]['FIXED LEADER']['SYSTEM BANDWIDTH {WB}']
        self.system_power =pd0.ensemble_data[en]['FIXED LEADER']['SYSTEM POWER {CQ}']
        self.tpp_hundredths =pd0.ensemble_data[en]['FIXED LEADER']['TPP HUNDREDTHS {TP}']          
#%%         

# fpath = r'P:\\41806287\\41806287 NORI-D Data\\Data\\Fixed Stations\\02_Fixed_Bottom_Current_Turbidity\\01_FBCT1\\01_ADCP_600kHz-24149\\Raw\\FBCT1_Modem_Download_02112022\\FBCT1_0308_02112022.000'

# fpath = r'P:\\41806287\\41806287 NORI-D Data\\Data\\Fixed Stations\\02_Fixed_Bottom_Current_Turbidity\\01_FBCT1\\01_ADCP_600kHz-24149\\Raw\\FBCT1_Modem_Download_17102022\\FBCT1_0422_-1102022.000'
# # fpath = r'P:\41806287\41806287 NORI-D Data\Data\Fixed Stations\02_Fixed_Bottom_Current_Turbidity\01_FBCT1\01_ADCP_600kHz-24149\Raw\FBCT1_Modem_Download_10102022\FBCT1_0741_10102022.000'
# fpath = r'P:\\41806287\\41806287 NORI-D Data\\Data\\Fixed Stations\\02_Fixed_Bottom_Current_Turbidity\\01_FBCT1\\01_ADCP_600kHz-24149\\Raw\\FBCT1_Modem_Download_19102022\\FBCT1_1911_19102022.000'

# #fpath = r'\\USDEN1-STOR.DHI.DK\Projects\41806287\41806287 NORI-D Data\Data\Fixed Stations\02_Fixed_Bottom_Current_Turbidity\02_FBCT2\01_ADCP_600kHz-24144\Raw\Data Dump 09192022\09192020_2130.000'
# #pd0 = Pd0(fpath, import_file = True)#, start = 2390, end = 16547)

# adcp = DataSet(fpath)

# t = adcp.get_ensemble_datetimes()
#%%
# # # # #fpath = r'\\USDEN1-STOR.DHI.DK\\Projects\\41806287\\Backups\\Raw_Data_Backup_Hidden_Gem\\ROV_data_HG\\ROVDive20220928\\DHIDive08004r.000'
# pd0_fpath = r'\\USDEN1-STOR.DHI.DK\\Projects\\41806287\\41806287 NORI-D Data\\Data\\ROV\\Island Pride\\ADCP\\Raw\\ADCP_24142_600kHz\\ROV_ADCP_27102022\\_RDI_027.000'

# pd0_fpath = r'\\USDEN1-STOR.DHI.DK\\Projects\\41806287\\41806287 NORI-D Data\\Data\\Fixed Stations\\03_Movable_Turbidity\\02_MT2\\01_ADCP_600kHz-24146\\Raw\\MTS2_000.000'
# # pd0 = Pd0(fpath, import_file = False,)# start = 2390, end = 16547)  # 2390
# # # pd0 = Pd0(fpath, import_file = True, start = 2390, end = 16547)  # 2390


# pd0_fpath = 'RDI_Combine_20181127_20190111_export.000'



# # # # pt3_fpath = '\\\\USDEN1-STOR.DHI.DK\\Projects\\41806287\\41806287 NORI-D Data\\Data\\ROV\\Island Pride HD14\\ADCP\\Config\\ROV_ADCP_20161_PT3.txt'


# pd0 = Pd0(pd0_fpath, import_file = True)#, start = 1, end = 5)
# e = pd0.ensemble_data
#%%
# f = open(pd0_fpath,'rb')

# print(f.read(2))
# print(f.read(2))
# print(f.read(2))
# print(f.read(2))
# f.close()

# f = open(pd0_fpath,'rb')


# f.close()
#%%

# #%%
# # pd0_filepath = r'\\USDEN1-STOR.DHI.DK\Projects\41806287\41806287 NORI-D Data\Data\Fixed Stations\02_Fixed_Bottom_Current_Turbidity\01_FBCT1\01_ADCP_600kHz-24149\Raw\FBCT1_Full_Download_17112022\FBCT1000.000'
# # pt3_filepath  =  r'\\USDEN1-STOR.DHI.DK\Projects\41806287\41806287 NORI-D Data\Data\Fixed Stations\02_Fixed_Bottom_Current_Turbidity\01_FBCT1\01_ADCP_600kHz-24149\Config_File\FBCT01_P3_TEST_17112022.txt'


# pd0_filepath = r'\\USDEN1-STOR.DHI.DK\Projects\41806287\41806287 NORI-D Data\Data\Fixed Stations\02_Fixed_Bottom_Current_Turbidity\01_FBCT1\01_ADCP_600kHz-24149\Raw\FBCT1_Full_Download_17112022\FBCT1000.000'
# # # # # pt3_filepath  =  r'\\USDEN1-STOR.DHI.DK\Projects\41806287\41806287 NORI-D Data\Data\Fixed Stations\02_Fixed_Bottom_Current_Turbidity\01_FBCT1\01_ADCP_600kHz-24149\Config_File\FBCT01_P3_TEST_17112022.txt'


# # # pt3_filepath = r'\\USDEN1-STOR.DHI.DK\Projects\41806287\41806287 NORI-D Data\Data\ROV\Island Pride HD14\ADCP\Config\ROV_ADCP_20161_PT3.txt'

# # # # pd0_filepath = r'\\USDEN1-STOR.DHI.DK\Projects\41806287\41806287 NORI-D Data\Data\Fixed Stations\04_Fixed_Turbidity\02_FT2\01_ADCP_600kHz-24157\Raw\FTS2_000.000'
# # # # pt3_filepath = r'\\USDEN1-STOR.DHI.DK\Projects\41806287\41806287 NORI-D Data\Data\Fixed Stations\04_Fixed_Turbidity\02_FT2\01_ADCP_600kHz-24157\Config_File\PT3.txt'
# # # # # pd0_filepath = r'C:\Users\anba\OneDrive - DHI\Desktop\Projects\NORI Post-Campaign\PCV ADCP\ADCP_PCV_Setup\CL16_\CL16_001.000'
# pd0_filepath = r'\\USDEN1-STOR.DHI.DK\Projects\41806287\41806287 NORI-D Data\Data\ROV\Island Pride HD14\ADCP\Raw\ADCP_24142_600kHz\ROV_ADCP_07102022\_RDI_000.000'
# # # # pd0 = Pd0(pd0_fpaths[0],import_file = False)#.write_pd0('test2')  
# # pd0_filepath = r'\\USDEN1-STOR.DHI.DK\\Projects\\41806287\\Backups\\Raw_Data_Backup_Hidden_Gem\\ROV_data_HG\ROVDive20221103\DHIDive28002r.000'                                                                                          
# pd0_filepath = r'\\USDEN1-STOR.DHI.DK\\Projects\\41806287\\Backups\\Raw_Data_Backup_Hidden_Gem\\ROV_data_HG\\ROVDive20221026\\DHIDive26002r.000'


# pd0 = Pd0(pd0_filepath, import_file = False)#,print_progress = False, start = 3535, end= 3539)
# ds = DataSet(pd0_filepath, import_file = True,print_progress = True)#, start = 2189, end= 2189)
# # print(ds.get_ensemble_numbers())
#plt.plot(np.diff(pd0.get_ensemble_numbers()))
# pd0_filepath = r'\\USDEN1-STOR.DHI.DK\\Projects\\41806287\\Backups\\Raw_Data_Backup_Hidden_Gem\\ROV_data_HG\\ROVDive20221021\\DHIDive22005r.000'
# #pd0_filepath = r'\\USDEN1-STOR.DHI.DK\Projects\41806287\41806287 NORI-D Data\Data\ROV\Island Pride HD14\ADCP\Raw\ADCP_24142_600kHz\ROV_ADCP_07102022\_RDI_013.000'
# # # pd0_filepath = r'\\USDEN1-STOR.DHI.DK\\Projects\\41806287\\Backups\\Raw_Data_Backup_Hidden_Gem\\ROV_data_HG\\ROVDive20220810\\test005r.000'
# pd0 = Pd0(pd0_filepath,import_file = False)
# #%%
