# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-31 22:34:42
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-17 14:21:36

import logging

def coronadata_logger() :
    return logging.getLogger("pycoronadata")

def coronatool_logger() :
    return logging.getLogger("coronatools")

def debug_mode() :
    coronadata_logger_debug_mode()
    coronatool_logger_debug_mode()

def coronadata_logger_debug_mode() :
    logger = coronadata_logger()
    logger_debug_mode(logger)

def coronatool_logger_debug_mode() :
    logger = coronatool_logger()
    logger_debug_mode(logger)

def logger_debug_mode(logger) :
    logger.setLevel(logging.DEBUG)  
    formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)       