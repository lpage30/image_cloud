# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# distutils: language = c++
# distutils: extra_compile_args = -std=c++11
from libcpp.atomic cimport atomic
cdef extern from "stdio.h":
    int printf(const char *format, ...) noexcept nogil

cdef atomic[int] g_level
g_level.store(LoggerLevel.NOT_SET)

cdef void set_logger_level(LoggerLevel level) noexcept nogil:
    g_level.store(level)

cdef int can_log(LoggerLevel level) noexcept nogil:
    if level >= g_level.load():
        return 1
    return 0

cdef int no_log(const char* format, ...) noexcept nogil:
    pass

cdef log_f log_error() noexcept nogil:
    if 1 == can_log(LoggerLevel.ERROR):
        return printf
    return no_log

cdef log_f log_warning() noexcept nogil:
    if 1 == can_log(LoggerLevel.WARNING):
        return printf
    return no_log

cdef log_f log_info() noexcept nogil:
    if 1 == can_log(LoggerLevel.INFO):
        return printf
    return no_log

cdef log_f log_debug() noexcept nogil:
    if 1 == can_log(LoggerLevel.DEBUG):
        return printf
    return no_log

cdef py_set_logger_level(int level):
    cdef LoggerLevel elevel
    if level == LoggerLevel.ERROR:
        elevel = LoggerLevel.ERROR
    elif level == LoggerLevel.WARNING:
        elevel = LoggerLevel.WARNING
    elif level == LoggerLevel.INFO:
        elevel = LoggerLevel.INFO
    elif level == LoggerLevel.DEBUG:
        elevel = LoggerLevel.DEBUG
    else:
        elevel = LoggerLevel.NOT_SET
    set_logger_level(elevel)