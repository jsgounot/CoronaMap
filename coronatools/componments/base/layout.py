# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-04-01 15:34:35
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-03 16:39:45

from componments.base.utils import BokehOverlayModel

class LayoutController(BokehOverlayModel) :

	def __init__(self, * args, ** kwargs) :
		self.on_change = {}

		if not all(isinstance(arg, str) for arg in args) :
			raise ValueError("* args must be a string")
		
		kwargs.update({arg : None for arg in args})
		self.setup_kwargs(kwargs)
		super().__init__()

	def __setattr__(self, attr, name) :
		super().__setattr__(attr, name)
		for fun in self.on_change.get(attr, []) :
			fun(attr, name)

	def setup_kwargs(self, kwargs) :
		for key, value in kwargs.items() :
			setattr(self, key, value)
		
	def add_on_change_fun(self, attribute, fun) :
		self.on_change.setdefault(attribute, []).append(fun)