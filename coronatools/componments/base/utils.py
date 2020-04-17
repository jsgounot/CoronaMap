# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-25 23:42:46
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-15 13:32:51

import logging
logger = logging.getLogger("coronatools")

class SignalControl() :

    def __init__(self) :
        self.signals_funs = {}

    def emit_signal(self, signal, * args, ** kwargs) :
        for fun in self.signals_funs.get(signal, []) :
            fun(* args, ** kwargs)

    def add_receiver(self, signal, fun) :
        self.signals_funs.setdefault(signal, []).append(fun)

class BokehOverlayModel(SignalControl) :

    def __init__(self) :
        super().__init__()

    def link_on_change(self, self_attr, select, select_attr="value", postfun=None) :
        def on_change(attr, old, new) :
            logger.debug(f"Get {new} to attr {self_attr} for {self}")
            if postfun : new = postfun(new)
            logger.debug(f"Set {new} to attr {self_attr} for {self}")
            setattr(self, self_attr, new)
        select.on_change(select_attr, on_change)

    def link_to_controller(self, self_attr, controller, controller_attr, postfun=None) :
        def on_change(new) :
            logger.debug(f"Get {new} to attr {self_attr} for {self}")
            if postfun : new = postfun(new)
            logger.debug(f"Set {new} to attr {self_attr} for {self}")
            setattr(self, self_attr, new)
        controller.add_receiver(controller_attr, on_change)

    def emit_change(self, attr_name) :
        self.emit_signal(attr_name, getattr(self, attr_name))

class BaseChart(BokehOverlayModel) :

    def __init__(self) :
        super().__init__()

    @property
    def figure(self):
        raise NotImplementedError()
    
    @property
    def xname(self) :
        return self.get_xaxis().axis_label
    
    @xname.setter
    def xname(self, xname) :
        self.get_xaxis().axis_label = xname

    @property
    def yname(self) :
        return self.get_yaxis().axis_label
    
    @yname.setter
    def yname(self, yname) :
        self.get_yaxis().axis_label = yname

    def get_xaxis(self, index=0) :
        return self.figure.xaxis[index]

    def get_yaxis(self, index=0) :
        return self.figure.yaxis[index]

class ToolTips() :

    def __init__(self, * args) :
        self.tips = []
        for arg in args :
            self.append(ToolTip.tip_from_arg(arg))

    def __iter__(self) :
        yield from self.tips

    def __contains__(self, name) :
        return any(name == tip.name for tip in self)

    def __getitem__(self, name) :
        try : return next(tip for tip in self if tip.name == name)
        except StopIteration : raise KeyError(f"Name not found in ToolTips : {name}")

    def append(self, tooltip) :
        if tooltip.name in self : raise ValueError(f"ToolTip with the same name already found : {tooltip.name}")
        self.tips.append(tooltip)

    def insert(self, idx, tooltip) :
        if tooltip.name in self : raise ValueError(f"ToolTip with the same name already found : {tooltip.name}")
        self.tips.insert(idx, tooltip)

    def bokeh_format(self) :
        return [tip.bokeh_format() for tip in self]

class ToolTip() :

    def __init__(self, name, description=None, format=None, lead="@") : 
        self.name = name
        self.description = description
        self.format = format
        self.lead = lead

    @classmethod
    def tip_from_arg(self, arg) :
        if isinstance(arg, ToolTip) : return arg
        if isinstance(arg, str) : return ToolTip(arg)
        if isinstance(arg, dict) : return ToolTip(** arg)
        return ToolTip(* arg)

    def bokeh_format(self) :
        description = self.description or self.name
        if self.format :
            return (f'{description}', f'{self.lead}{self.name}{{{self.format}}}')
        else :
            return (f'{description}', f'{self.lead}{self.name}')
