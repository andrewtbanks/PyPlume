# -*- coding: utf-8 -*-
from datetime import datetime
import cycler
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as mpl_path_effects

#class plotting:
    
dhi_blue1 = '#04426e'
dhi_blue2 = '#4d9ab3'
dhi_blue3 = '#0493b2'
dhi_blue4 = '#c3dde5'
dhi_green1 = '#01be62'
dhi_green2 = '#00b591'
dhi_green3 = '#6ad6af'


dhi_gray1 = '#c4c4c4'
dhi_gray2 = '#8b8b8c'
dhi_gray3 = '#686c6e'

dhi_red1= '#c81f00'
dhi_red2 = '#ac1817'

dhi_yellow1 = '#ffbb3c'
dhi_yellow2 = '#ebd844'

dhi_orange1 = '#ec8833'
dhi_orange2 = '#d3741c'


class dhi_colors:
    blue1 = '#04426e'
    blue2 = '#4d9ab3'
    blue3 = '#0493b2'
    blue4 = '#c3dde5'
    
    green1 = '#93c47d' #'#01be62'
    green2 = '#00b591'
    green3 = '#6ad6af'
    
    gray1 = '#c4c4c4'
    gray2 = '#8b8b8c'
    gray3 = '#686c6e'

    red1= '#c81f00'
    red2 = '#ac1817'

    yellow1 = '#ffbb3c'
    dhi_yellow2 = '#ebd844'

    orange1 = '#ec8833'
    orange2 = '#d3741c'
    
    
    
    




mpl.rcParams['font.size'] = 9
mpl.rcParams['lines.linewidth'] = 2
mpl.rcParams['lines.color'] = 'black'
#mpl.rcParams['axes.grid'] = True
mpl.rcParams['patch.edgecolor'] = 'white'
mpl.rcParams['axes.grid.which'] = 'major'
mpl.rcParams['lines.markersize'] = 1.6
mpl.rcParams['ytick.labelsize'] = 8
mpl.rcParams['xtick.labelsize'] = 8

mpl.rcParams['ytick.labelright'] = False
mpl.rcParams['xtick.labeltop'] = False

mpl.rcParams['ytick.right'] = True
mpl.rcParams['xtick.top'] = True
mpl.rcParams['ytick.major.right'] = True
mpl.rcParams['xtick.major.top'] = True


# #mpl.rcParams['text.latex.preamble']=[r"\usepackage{lmodern}"]

# params = {'text.usetex' : True,
#           'font.size' : 11,
#           'font.family' : 'lmodern',
#           'text.latex.unicode': True,
#           }
# mpl.rcParams.update(params) 

# mpl.rcParams['axes.titlepad']: 250
# mpl.rcParams['axes.labelpad']: 250
mpl.rcParams['axes.labelweight'] = 'normal'

mpl.rcParams['legend.fontsize'] = 8
mpl.rcParams['legend.framealpha']= 0.5

mpl.rcParams['axes.titlesize'] = 12
mpl.rcParams['axes.titleweight'] ='normal'

mpl.rcParams['font.family'] ='TImes New Roman'
#rcParams['font.family'] = 'Georgia'

mpl.rcParams['axes.labelsize'] = 10
mpl.rcParams['axes.linewidth'] = 1.25

mpl.rcParams['xtick.major.size'] = 5.0
mpl.rcParams['xtick.minor.size'] = 3.0
mpl.rcParams['ytick.major.size'] = 5.0
mpl.rcParams['ytick.minor.size'] = 3.0


mpl.rcParams['figure.dpi'] : 300.0



# blues  = ['#9ecae1','#6baed6','#4292c6','#2171b5']#,'#08519c']
# greens = ['#c7e9c0','#a1d99b','#74c476','#41ab5d']#,'#238b45']
# colors = []
# for i in range(len(blues)):
#     colors.append(blues[-(i+1)])
#     colors.append(greens[-(i+1)])

colors = 2*['#283747','#0051a2', '#41ab5d', '#feb24c', '#93003a']
line_style = 5*['-'] + 5*['--']
mpl.rcParams['axes.prop_cycle'] = cycler.cycler('color',colors) +cycler.cycler('linestyle',line_style)

alpha = 0.7
to_rgba = mpl.colors.ColorConverter().to_rgba#
color_list=[]
for i, col in enumerate(mpl.rcParams['axes.prop_cycle']):
    color_list.append(to_rgba(col['color'], alpha))
mpl.rcParams['axes.prop_cycle'] = cycler.cycler(color=color_list)


mpl.rcParams['xtick.direction'] = 'in'
mpl.rcParams['ytick.direction'] = 'in'


    

def subplots(**kwargs):
    
    if kwargs.get('figheight'): figheight = kwargs.get('figheight')
    else: figheight = 4.25*(1+(5**.5))/2
    
    if kwargs.get('figwidth'): figwidth = kwargs.get('figwidth')
    else: figwidth = figheight
    
    
    if kwargs.get('nrow'): nrow = kwargs.get('nrow')
    else: nrow = 1
    
    if kwargs.get('ncol'): ncol = kwargs.get('ncol')
    else: ncol = 1    
    
    if kwargs.get('sharex'): sharex = kwargs.get('sharex')
    else: sharex = False   
    
    if kwargs.get('sharey'): sharey = kwargs.get('sharey')
    else: sharey = False 
    
    if kwargs.get('width_ratios'): width_ratios = kwargs.get('width_ratios')
    else: width_ratios = [1]*ncol

    if kwargs.get('height_ratios'): height_ratios = kwargs.get('height_ratios')
    else: height_ratios = [1]*nrow   
    
    
    if kwargs.get('watermark_text') : watermark_text = kwargs.get('watermark_text')
    else: watermark_text = 'PRELIMINARY RESULTS \n INTERNAL CIRCULATION ONLY'
    
    
    
    fig,axs = plt.subplots(figsize = (figwidth,figheight),
                           nrows = nrow,
                           ncols = ncol,
                           gridspec_kw={'width_ratios': width_ratios,
                                        'height_ratios': height_ratios},
                           sharex = sharex,
                           sharey = sharey)


  
    def add_watermark(ax, add_date = True):
        # add a watermark and some metadata to the axes
        path_effects=[mpl_path_effects.Stroke(linewidth=2, foreground="black",alpha = 0.035)] 
        ax.text(.5, .5, watermark_text, transform=ax.transAxes,fontsize=15, color='gray', alpha=.1,ha='center', va='center', rotation=0,path_effects = path_effects,fontname = 'Arial',zorder = 1)
        if add_date:
            ax.text(.985, 0.02,os.getlogin() + '\n' + datetime.now().strftime("%d/%m/%y %H:%M"), transform=ax.transAxes,fontsize=6, color='black', alpha=0.4,ha='right', va='bottom', rotation=0, weight = 'bold',fontname = r'Arial',zorder = 1)
        return ax
    
    
 
    def set_ax_params(ax):
        
            # if not kwargs.get('for_production'):
            #     ax = add_watermark(ax)
            # else: ax = add_watermark(axs)
            
            # ax.xaxis.set_major_locator(mpl.ticker.AutoLocator())
            # ax.yaxis.set_major_locator(mpl.ticker.AutoLocator())
            
            # ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator())
            # ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator())

            ax.grid(alpha = 0.25)
        
    
    if nrow*ncol>1:
        
        for i,ax in enumerate(axs.reshape(-1)): 
            set_ax_params(ax)
            
    else:
        set_ax_params(axs)
            

        
                

             
       

    
    

                    
 

    plt.tight_layout(rect = [0.025,0.1,0.975,.9])
    return fig,axs





