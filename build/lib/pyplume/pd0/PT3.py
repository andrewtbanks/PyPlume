# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 16:34:15 2023

@author: anba
"""

class PT3:
    # class to manage PT3 teste results. Only parsing High Gain RSSI implemented
    # currently.
    def __init__(self,filepath):
        self.filepath = filepath
        self.k_c = self.read()
    def read(self):
        """
        Read the High Gain RSSI parameters from a TRDI PT3 calibration test file

        Parameters
        ----------
        path : string
            path to the .txt file containing PT3 test data

        Returns
        -------
        k_c : dict
            dictionary containign the parsed RSSI parameters for each beam 

        """
        file = open(self.filepath,'r')
        for i,line in enumerate(file.readlines()):
            L = [i for i in line.split(' ') if i]
        
            if ' '.join(L[:3]) == 'High Gain RSSI:':
                k_c = { 1: float(L[3])/100,# beam 1
                        2: float(L[4])/100,# beam 2
                        3: float(L[5])/100,# beam3
                        4: float(L[6].replace('\n',''))/100}# beam4  
        file.close()
        return k_c