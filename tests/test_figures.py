import importlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def test_depth_histogram_visible_stacks_include_events_across_thresholds():
    module=importlib.import_module('earthquake_explorer.figures')
    frame=pd.DataFrame({'depth':[69,69,71,71,71,71,299,301],
        'depth_class':['Shallow','Shallow','Intermediate','Intermediate','Intermediate','Intermediate','Intermediate','Deep']})
    fig,ax=plt.subplots()
    try:
        module.draw_depth_histogram(ax,frame,np.array([68,79,290,310]))
        tops={}
        for patch in ax.patches:
            x=round(patch.get_x(),6)
            tops[x]=max(tops.get(x,0),patch.get_y()+patch.get_height())
        assert sorted(tops.values()) == [0,2,6]
    finally:
        plt.close(fig)
