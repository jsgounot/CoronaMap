# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-04-05 11:56:24
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-15 13:27:51

import copy
from collections import namedtuple
from bokeh.models.widgets import Tabs, Panel

from componments.base.errors import InternalError

class PanelAxisTypes() :

    """    
    A single class to mix similar plots but with different ax types (linear, log for example)
    The current solution is convenient but is not efficient, each plot are unique and everything is duplicated
    A better solution would be to be able to change ax type on figure, which is not currently available
    see : https://discourse.bokeh.org/t/dynamic-change-scale-from-linear-to-log/5100/3
    Or to share a specific number of function and arguments (for example : source), but would need a specific work for each
    class (maybe using inheritence)
    """

    dat = default_axis_type = namedtuple("PanelAxisTypeInfo", ["title", "x", "y", "kwargs"],
        defaults=["linear", "linear", {}])

    def __init__(self, master_class, axis_types, * args, ** kwargs) :
        instances = []
        panels = []

        for axis_type in axis_types :
            if not isinstance(axis_type, PanelAxisTypes.dat) :
                raise ValueError(f"axis_types must be of type PanelAxeTypes.default_axis_type, got {type(axis_type)}")

            # need to make a copy, otherwise kwargs might be alterned from en init method
            instance_kwargs = copy.deepcopy(kwargs)
            subkwargs = {"x_axis_type" : axis_type.x, "y_axis_type" : axis_type.y, ** axis_type.kwargs}
            instance_kwargs.update(subkwargs)

            instance = master_class(* args, ** instance_kwargs)
            instances.append(instance)

            panel = Panel(child=instance.figure, title=axis_type.title)
            panels.append(panel)

        if not instances :
            raise ValueError("Cannot create an empty PanelAxisTypes instance")

        self._instances = instances
        self._tabs = Tabs(tabs=panels)
        self._fun_name = None

    def __setattr__(self, name, value) :
        # condition order is important here !

        init = ("_instances", "_tabs", "_fun_name")
        if name in init : 
            super().__setattr__(name, value)
        
        # Maybe an other way should be better
        # but hasattr does not work since we override getattr
        # to return instances values
        elif name in self.__dict__ :
            super().__setattr__(name, value)    

        else : 
            for instance in self._instances :
                setattr(instance, name, value)

    def __getattr__(self, name) :
        obj = getattr(self._instances[0], name)

        if callable(obj) :
            self._fun_name = name
            return self.wrapper_function

        return obj

    def wrapper_function(self, * args, ** kwargs) :
        if self._fun_name is None : raise InternalError("fun_name cannot be set to None")
        for instance in self._instances :
            getattr(instance, self._fun_name)(* args, ** kwargs)
    
    @property
    def tabs(self):
        return self._tabs
    
    @property
    def figure(self):
        # This one should be removed 
        # but was abused for testing
        return self._tabs
    
    @staticmethod
    def axis_type(* args, ** kwargs) :
        return PanelAxisTypes.dat(* args, ** kwargs)