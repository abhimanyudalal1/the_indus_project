import numpy as np
from sklearn.linear_model import LinearRegression

def base(precip, snow, et, time, temp, alpha, beta, delta, dd=None):
    q_rain = alpha*precip(time)
    
    dd = np.maximum(temp-273, 0)
    q_melt = beta* snow[time-2]*dd[time-2]

    q_loss = delta*et

    

    



    
    
