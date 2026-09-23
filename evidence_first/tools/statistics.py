from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Difference:
    absolute:float
    relative:float|None

def difference(baseline:float,observed:float)->Difference:
    return Difference(observed-baseline,None if baseline==0 else (observed-baseline)/baseline)

def weighted_mean(values:list[float],weights:list[float])->float:
    if len(values)!=len(weights) or not values: raise ValueError('values and weights must be same nonzero length')
    total=sum(weights)
    if total==0: raise ValueError('weights sum to zero')
    return sum(v*w for v,w in zip(values,weights))/total

def slope(xs:list[float],ys:list[float])->float:
    if len(xs)!=len(ys) or len(xs)<2: raise ValueError('need paired observations')
    mx=sum(xs)/len(xs); my=sum(ys)/len(ys); den=sum((x-mx)**2 for x in xs)
    if den==0: raise ValueError('x variance is zero')
    return sum((x-mx)*(y-my) for x,y in zip(xs,ys))/den
