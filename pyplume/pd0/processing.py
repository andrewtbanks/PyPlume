# -*- coding: utf-8 -*-
"""
Created on Fri Jul 21 15:45:10 2023

@author: anba
"""
import numpy as np


class processing:
    
    def __init__(self,pd0):
        
        self._pd0 = pd0
        
        self.ensemble_fields = ['ECHO INTENSITY','CORRELATION MAGNITUDE','PERCENT GOOD'] # keys for fields defined in ensemble data. Can be modified by append_to_ensembles method
        
        
        #vectorize some functions
        self.water_absorption_coeff = np.vectorize(self._scalar_water_absorption_coeff)
        self.sediment_absorption_coeff = np.vectorize(self._scalar_sediment_absorption_coeff)   
        self.counts_to_absolute_backscatter = np.vectorize(self._scalar_counts_to_absolute_backscatter)


    # def ABS_to_NTU(self,ABS, A, B):
    #     '''
    #     Convert ABS to NTU using the equation 10log(SSC) = A*Backscatter + B.
    
    #     Parameters
    #     ----------
    #     ABS : numpy.ndarray
    #         Absolute backscatter values
    #     A : float
    #         Coefficient A in the equation.
    #     B : float
    #         Coefficient B in the equation.
    
    #     Returns
    #     -------
    #     numpy.ndarray
    #         Nephelometric Turbidity Units (NTU) calculated from ABS.
    #     '''
    
    #     ABS[ABS >= 32768] = np.nan
    #     return (1 / 10) * 10**(A * ABS + B) 
    
    # def NTU_to_SSC(self,NTU,A):
    #     '''
    #     Convert NTU to SSC using equation SCC = A*NTU
    
    #     Parameters
    #     ----------
    #     NTU : numpy.ndarray
    #         Absorption values.
    #     A : float
    #         Coefficient A in the equation.
    
    
    #     Returns
    #     -------
    #     numpy.ndarray
    #         Suspended solids concentration (SSC) calcualted from NTU
    #     '''
    #     return A*NTU 
    def mask_bottom_track(self, cell_offset = 0):
        # create a mask based on ADCP bottom track 
        
        # cell offset is number of cells to mask above (positive) or below (negative) the bottom-track cell. 
        # Mask bottom track
        offset_distance = self._pd0.config.depth_cell_length*cell_offset
        
        bt_range = self._pd0.get_bottom_track()
        if any(~np.isnan(bt_range).flatten()):
            bt_range = np.repeat(bt_range[:, np.newaxis, :], self._pd0.config.number_of_cells, axis=1)
            bt_range[bt_range == 0] = 32675
            bin_centers = np.outer(self._pd0.geometry.get_bin_midpoints(), np.ones(self._pd0.n_ensembles))
            bin_centers = np.repeat(bin_centers[np.newaxis, :, :], self._pd0.config.number_of_beams, axis=0)
            mask = (bt_range - self._pd0.config.depth_cell_length / 100) > (bin_centers- cell_offset)
            self._pd0.mask.define_mask(mask=mask, name='bottom track', set_active=True)
            
            

         
    def _scalar_counts_to_absolute_backscatter(self,E,E_r,k_c,alpha,C,R,Tx_T, Tx_PL, P_DBW):
        """
        Absolute Backscatter Equation from Deines (Updated - Mullison 2017 TRDI Application Note FSA031)
    
        Parameters
        ----------
        E_r : float
            Measured RSSI amplitude in the absence of any signal (noise), in counts.
        C : float
            Constant combining several parameters specific to each instrument.
        k_c : float
            Factor to convert amplitude counts to decibels (dB).
        E : float
            Measured Returned Signal Strength Indicator (RSSI) amplitude, in counts.
        Tx_T : float
            Tranducer temperature in deg C.
        R : float
            Along-beam range to the measurement in meters
        alpha : float
            Acoustic absorption (dB/m). 
        Tx_PL : float
            Transmit pulse length in dBm.
        P_DBW : float
            Transmit pulse power in dBW.
    
        Returns
        -------
        tuple
            Tuple containing two elements:
            - Sv : float
                Apparent volume scattering strength.
            - StN : float
                True signal to noise ratio.
    
        Notes
        -----
        - The use of the backscatter equation should be limited to ranges beyond π/4 * Rayleigh Distance for the given instrument.
        - Rayleigh Distance is calculated as transmit pulse length * α / width, representing the distance at which the beam can be considered to have fully formed.
        - For further details, refer to the original documentation by Deines.
        - 𝑘_c is a factor used to convert the amplitude counts reported by the ADCP’s receive circuitry to decibels (dB).
        - 𝐸 is the measured Returned Signal Strength Indicator (RSSI) amplitude reported by the ADCP for each bin along each beam, in counts.
        - 𝐸_r is the measured RSSI amplitude seen by the ADCP in the absence of any signal (the noise), in counts, and which is constant for a given ADCP.
        """
        StN = (10**(k_c * E / 10) - 10**(k_c * E_r / 10)) / (10**(k_c * E_r / 10))
        L_DBM = 10 * np.log10(Tx_PL)
        #P_DBW = 10 * np.log10(Tx_Pw)
        Sv = C + 10 * np.log10((Tx_T + 273.16) * (R**2)) - L_DBM - P_DBW + 2 * alpha * R + 10 * np.log10((10**(0.1 * k_c * (E - E_r)) - 1))
    
        return Sv, StN
    
       
        
    def _scalar_water_absorption_coeff(self,T, S, z, f, pH):
        '''
        Calculate water absorption coefficient.
    
        Parameters
        ----------
        T : float
            Temperature in degrees Celsius.
        S : float
            Salinity in practical salinity units (psu).
        z : float
            Depth in meters.
        f : float
            Frequency in kHz.
        pH : float
            Acidity.
    
        Returns
        -------
        float
            Water absorption coefficient in dB/km.
        '''
        c = 1449.2 + 4.6 * T - 0.055 * T**2 + 0.00029 * T**3 + (0.0134 * T) * (S - 35) + 0.016 * z
        #c = 1412 + 3.21 * T + 1.19 * S + 0.0167 * z
    
        # Boric acid component
        A1 = (8.68 / c) * 10**(0.78 * pH - 5)
        P1 = 1
        f1 = 2.8 * ((S / 35)**0.5) * 10**(4 - (1245 / (273 + T)))
    
        # Magnesium sulphate component
        A2 = 21.44 * (S / c) * (1 + 0.025 * T)
        P2 = 1 - (1.37e-4) * z + (6.2e-9) * z**2
        f2 = (8.17 * 10**(8 - (1990 / (273 + T)))) / (1 + 0.0018 * (S - 35))
    
        if T <= 20:
            A3 = (4.937e-4) - (2.59e-5) * T + (9.11e-7) * T**2 - (1.5e-8) * T**3
        elif T > 20:
            A3 = (3.964e-4) - (1.146e-5) * T + (1.45e-7) * T**2 - (6.5e-8) * T**3
        P3 = 1 - (3.83e-5) * z + (4.9e-10) * (z**2)
    
        # Calculate water absorption coefficient
        alpha_w = (A1 * P1 * f1 * (f**2) / (f**2 + f1**2) + A2 * P2 * f2 * (f**2) / (f**2 + f2**2) + A3 * P3 * (f**2))
        
        # Convert absorption coefficient to dB/km
        alpha_w = (1 / 1000) * alpha_w
        
        return alpha_w
    
    
    def _scalar_sediment_absorption_coeff(self,ps, pw, d, SSC, T,S, f,z):
        '''
        Calculate sediment absorption coefficient.
    
        Parameters
        ----------
        ps : float
            Particle density in kg/m^3.
        pw : float
            Water density in kg/m^3.
        d : float
            Particle diameter in meters.
        SSC : float
            Suspended sediment concentration in kg/m^3.
        T : float
            Temperature in degrees Celsius.
        f : float
            Frequency in kHz .
    
        Returns
        -------
        float
            Sediment absorption coefficient.
        '''
        c = 1449.2 + 4.6 * T - 0.055 * T**2 + 0.00029 * T**3 + (0.0134 * T) * (S - 35) + 0.016 * z # speed of sound in water
        v = (40e-6) / (20 + T)  # Kinematic viscosity (m2/s)
        B = (np.pi * f / v) * 0.5
        delt = 0.5 * (1 + 9 / (B * d))
        sig = ps / pw
        s = 9 / (2 * B * d) * (1 + (2 / (B * d)))
        k = 2 * np.pi / c  # Wave number (Assumed, as it isn't defined in the paper)
    
        alpha_s = (k**4) * (d**3) / (96 * ps) + k * ((sig - 1)**2) / (2 * ps) + \
                  (s / (s**2 + (sig + delt)**2)) * (20 / np.log(10)) * SSC
    
        return alpha_s     

        

    def calculate_absolute_backscatter(self,**kwargs):
        """
        Convert numpy array of ensemble data of echo intensity to absolute backscatter then added to ensemble_data property of the WorkhorseADCP class.
    
        Optional Args:
            E_r
            k_c
            C
            alpha 
            P_dbw
     
        """
    
    
        E_r = 39 # noise floor 
        
        ## select C based on WB commmand (0 = 25%, 1 = 6.25%)
        WB = self._pd0.ensemble_data[0]['FIXED LEADER']['SYSTEM BANDWIDTH {WB}']
        if WB==0:
            C = -139.09 #for Workhorse 600, 25% 
        else:
            C = -149.14 # for Workhorse 600, 6%
        # Beam High Gain RSSI
        
        if hasattr(self._pd0,'PT3'):
            k_c = self._pd0.PT3.k_c
        else:
            k_c = {1: 0.3931,# beam 1
                    2: 0.4145,# beam 2
                    3: 0.416,# beam3
                    4: 0.4129}# beam4
        if self._pd0.ensemble_data[0]["SYSTEM CONFIGURATION"]["FREQUENCY"] == '300-kHz':
            alpha = 0.068 #nominal ocean value for a 600 kHz unit 
            P_dbw = 14 #battery supply power for Workhorse 300
            print('300 kHz Unit')
        elif self._pd0.ensemble_data[0]["SYSTEM CONFIGURATION"]["FREQUENCY"] == '600-kHz':
            alpha =  0.178 #nominal ocean value for a 600 kHz unit 
            P_dbw = 9 #battery supply power for Workhorse 600
            
        elif self._pd0.ensemble_data[0]["SYSTEM CONFIGURATION"]["FREQUENCY"] == '75-kHz':
            alpha =  0.027 #nominal ocean value for a 600 kHz unit 
            P_dbw = 27.3 #battery supply power for Workhorse 600
            
            
        # overwrite defaults with kwarg parameters 
        E_r = kwargs.pop('E_r',E_r) 
        C = kwargs.pop('C',C)
        k_c = kwargs.pop('k_c',k_c)
        alpha = kwargs.pop('alpha',alpha)
        P_dbw = kwargs.pop('P_dbw',P_dbw)
        
    
        #get other instrument data
        temperature = np.outer(self._pd0.get_sensor_temperature(),np.ones(self._pd0.config.number_of_cells)).T
        bin_distances = np.outer(self._pd0.geometry.get_bin_midpoints(),np.ones(self._pd0.n_ensembles))#/np.cos(20*np.pi/180)#/100
        transmit_pulse_lengths = np.outer(self._pd0.get_sensor_transmit_pulse_lengths(),np.ones(self._pd0.config.number_of_cells)).T#/100
        E = self._pd0.get_ensemble_array(field_name = 'ECHO INTENSITY') #echo intensity array 
        
        # initalize arrays  
        X = np.empty((self._pd0.config.number_of_beams,self._pd0.config.number_of_cells,self._pd0.n_ensembles))
        StN = np.empty((self._pd0.config.number_of_beams,self._pd0.config.number_of_cells,self._pd0.n_ensembles))
    
        for beam in range(self._pd0.config.number_of_beams):
            # StN[beam,:,:] = (10**(k_c[beam+1]*E[beam,:,:]/10) - 10**(k_c[beam+1]*E_r/10))/10**(k_c[beam+1]*E_r/10)
            # X[beam,:,:] = C + 10*np.log10((temperature + 273.16)*(bin_distances**2)) - 10*np.log10(transmit_pulse_lengths) - P_dbw + 2*alpha*bin_distances + 10*np.log10(10**(k_c[beam+1]*(E[beam,:,:] - E_r)/10)-1)
            
            sv,stn =self.counts_to_absolute_backscatter(E = E[beam],
                                                        E_r = E_r,
                                                        k_c= k_c[beam+1],
                                                        alpha = alpha,
                                                        C = C,
                                                        R = bin_distances,
                                                        Tx_T = temperature,
                                                        Tx_PL = transmit_pulse_lengths,
                                                        P_DBW = P_dbw)

            
            StN[beam] = stn
            X[beam] = sv
            
            
            #X[beam,:,:] = C + 10*np.log10((temperature*bin_distances**2)/(transmit_pulse_lengths*P_dbw)) + 2*alpha*bin_distances + k_c[beam+1]*(E[beam,:,:] - E_r)
        self.append_to_ensembles(X,'ABSOLUTE BACKSCATTER')
        self.append_to_ensembles(StN,'SIGNAL TO NOISE RATIO')   
        
        
        
        
    def append_to_ensembles(self,X,title,nan_value = 32768):
        """
        Format numpy array of ensemble data into a list then add to ensemble_data property of the WorkhorseADCP class.
        Input array must have dimensions of (n_beams,nbins,n_ensemles). In a typical use case, ensemble data is manipulated in 
        array format, then appended to the ensemble_data property and written to a PD0 file. 
        Args:
            X: numpy array with dimensions (n_bins,n_ensembles,n_beams)
            title: (string) title for the formatted data when appended to the ensemble_data property of the WorkhorseADCP class object. 
            nan_value: (int) value to use in place of nan. 32768 is default. 
        """
        self.ensemble_fields.append(title) # update the list of ensemble field names
        for e in range(self._pd0.n_ensembles):
            ensemble_data = [] # data in the current ensemble
            for b in range(self._pd0.config.number_of_cells):
                bin_data = [] # data in the current bin
                for bm in range(self._pd0.config.number_of_beams):
                    
                    val = X[bm,b,e]
                    #bin_data.append(int(val))
                    try:
                        bin_data.append(int(val))
                    except:
                        bin_data.append(nan_value)
                        
                        
                ensemble_data.append(bin_data)
            self._pd0.ensemble_data[e][title] = ensemble_data  