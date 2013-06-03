# ----------------------------------------------------------------------
#  Copyright (C) 2012  Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

import functools
import logging
import time
import traceback


# TODO Need unit tests



###############################################################################
def logExceptions(getLoggerCallback=logging.getLogger):
  """ Returns a closure suitable for use as function/method decorator for
  logging exceptions that leave the scope of the decorated function. Exceptions
  are logged at ERROR level.

  getLoggerCallback:    user-supplied callback function that takes no args and
                          returns the logger instance to use for logging.

  Usage Example:
    NOTE: logging must be initialized *before* any loggers are created, else
      there will be no output; see nupic.support.initLogging()

    @logExceptions()
    def myFunctionFoo():
        ...
        raise RuntimeError("something bad happened")
        ...
  """

  def exceptionLoggingDecorator(func):

    @functools.wraps(func)
    def exceptionLoggingWrap(*args, **kwargs):
      try:
        return func(*args, **kwargs)
      except Exception, e:
        getLoggerCallback().exception(
          "Unhandled exception %r from %r. Caller stack:\n%s",
          e, ''.join(traceback.format_stack()), func)
        raise

    return exceptionLoggingWrap

  return exceptionLoggingDecorator


###############################################################################
def logEntryExit(getLoggerCallback=logging.getLogger,
                 entryExitLogLevel=logging.DEBUG, logArgs=False,
                 logTraceback=False):
  """ Returns a closure suitable for use as function/method decorator for
  logging entry/exit of function/method.

  getLoggerCallback:    user-supplied callback function that takes no args and
                          returns the logger instance to use for logging.
  entryExitLogLevel:    Log level for logging entry/exit of decorated function;
                          e.g., logging.DEBUG; pass None to disable entry/exit
                          logging.
  logArgs:              If True, also log args
  logTraceback:         If True, also log Traceback information

  Usage Examples:
    NOTE: logging must be initialized *before* any loggers are created, else
      there will be no output; see nupic.support.initLogging()

    @logEntryExit()
    def myFunctionBar():
        ...


    @logEntryExit(logTraceback=True)
    @logExceptions()
    def myFunctionGamma():
        ...
        raise RuntimeError("something bad happened")
        ...
  """

  def entryExitLoggingDecorator(func):

    @functools.wraps(func)
    def entryExitLoggingWrap(*args, **kwargs):

      if entryExitLogLevel is None:
        enabled = False
      else:
        logger = getLoggerCallback()
        enabled = logger.isEnabledFor(entryExitLogLevel)

      if not enabled:
        return func(*args, **kwargs)
      
      funcName = str(func)
      
      if logArgs:
        argsRepr = ', '.join(
          [repr(a) for a in args] +
          ['%s=%r' % (k,v,) for k,v in kwargs.iteritems()])
      else:
        argsRepr = ''
      
      logger.log(
        entryExitLogLevel, "ENTERING: %s(%s)%s", funcName, argsRepr,
        '' if not logTraceback else '; ' + repr(traceback.format_stack()))

      try:
        return func(*args, **kwargs)
      finally:
        logger.log(
          entryExitLogLevel, "LEAVING: %s(%s)%s", funcName, argsRepr,
          '' if not logTraceback else '; ' + repr(traceback.format_stack()))
    
    
    return entryExitLoggingWrap

  return entryExitLoggingDecorator


###############################################################################
def retry(timeoutSec, initialRetryDelaySec, maxRetryDelaySec,
          retryExceptions=(Exception,),
          retryFilter=lambda e, args, kwargs: True,
          getLoggerCallback=None, clientLabel=""):
  """ Returns a closure suitable for use as function/method decorator for
  retrying a function being decorated.
  
  timeoutSec:           How many seconds from time of initial call to stop 
                        retrying (floating point); 0 = no retries
  initialRetryDelaySec: Number of seconds to wait for first retry.
                        Subsequent retries will be at the lesser of twice
                        this amount or maxRetryDelaySec (floating point)
  maxRetryDelaySec:     Maximum amount of seconds to wait between retries
                        (floating point)
  retryExceptions:      A tuple (must be a tuple) of exception classes that,
                        including their subclasses, should trigger retries;
                        Default: any Exception-based exception will trigger 
                        retries
  retryFilter:          Optional filter function used to further filter the
                        exceptions in the retryExceptions tuple; called if the
                        current exception meets the retryExceptions criteria: 
                        takes the current exception instance, args, and kwargs 
                        that were passed to the decorated function, and returns
                        True to retry, False to allow the exception to be
                        re-raised without retrying. Default: permits any
                        exception that matches retryExceptions to be retried.
  getLoggerCallback:    User-supplied callback function that takes no args and
                        returns the logger instance to use for logging.
                        None=default "get logger": logging.getLogger.

  Usage Example:
    NOTE: logging must be initialized *before* any loggers are created, else
      there will be no output; see nupic.support.initLogging()
    
    _retry = retry(timeoutSec=300, initialRetryDelaySec=0.2, maxRetryDelaySec=10,
                   retryExceptions=[socket.error])
    @_retry
    def myFunctionFoo():
        ...
        raise RuntimeError("something bad happened")
        ...
  """
  
  assert initialRetryDelaySec > 0, str(initialRetryDelaySec)
  
  assert timeoutSec >= 0, str(timeoutSec)
  
  assert maxRetryDelaySec >= initialRetryDelaySec, \
      "%r < %r" % (maxRetryDelaySec, initialRetryDelaySec)
  
  assert isinstance(retryExceptions, tuple), (
    "retryExceptions must be tuple, but got %r") % (type(retryExceptions),)
  
  if getLoggerCallback is None:
    getLoggerCallback = logging.getLogger

  def retryDecorator(func):

    @functools.wraps(func)
    def retryWrap(*args, **kwargs):
      numAttempts = 0
      delaySec = initialRetryDelaySec
      startTime = time.time()
      
      # Make sure it gets called at least once
      while True:
        numAttempts += 1
        try:
          result = func(*args, **kwargs)
        except retryExceptions, e:
          if not retryFilter(e, args, kwargs):
            logger = getLoggerCallback()
            if logger.isEnabledFor(logging.DEBUG):
              logger.debug(
                '[%s] Failure in %r; retries aborted by custom retryFilter. '
                'Caller stack:\n%s', clientLabel, func,
                ''.join(traceback.format_stack()), exc_info=True)
            raise
          
          now = time.time()
          # Compensate for negative time adjustment so we don't get stuck
          # waiting way too long (python doesn't provide monotonic time yet)
          if now < startTime:
            startTime = now
          if (now - startTime) >= timeoutSec:
            getLoggerCallback().exception(
              '[%s] Exhausted retry timeout (%s sec.; %s attempts) for %r. '
              'Caller stack:\n%s', clientLabel, timeoutSec, numAttempts, func,
              ''.join(traceback.format_stack()))
            raise
          
          if numAttempts == 1:
            getLoggerCallback().warning(
              '[%s] First failure in %r; initial retry in %s sec.; '
              'timeoutSec=%s. Caller stack:\n%s', clientLabel, func, delaySec,
              timeoutSec, ''.join(traceback.format_stack()), exc_info=True)
          else:
            getLoggerCallback().debug(
              '[%s] %r failed %s times; retrying in %s sec.; timeoutSec=%s. '
              'Caller stack:\n%s',
              clientLabel, func, numAttempts, delaySec, timeoutSec,
              ''.join(traceback.format_stack()), exc_info=True)
              
              
            time.sleep(delaySec)
            
            delaySec = min(delaySec*2, maxRetryDelaySec)
        else:
          if numAttempts > 1:
            getLoggerCallback().info('[%s] %r succeeded on attempt # %d',
                                     clientLabel, func, numAttempts)
            
          return result
    
    
    return retryWrap

  return retryDecorator