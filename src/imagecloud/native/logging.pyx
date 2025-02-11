# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# distutils: language = c++
# distutils: extra_compile_args = -std=c++11
cdef extern from "<stdlib.h>":
    ctypedef unsigned int size_t
    void* malloc(size_t size) noexcept nogil
    void free(void* ptr) noexcept nogil
cdef extern from "stdarg.h":
    ctypedef struct __va_list_tag:
        pass
    ctypedef __va_list_tag* va_list
    void va_start(va_list ap, ...) noexcept nogil
    void va_end(va_list ap) noexcept nogil
    int vsnprintf(char *str, unsigned int size, const char *format, va_list ap) noexcept nogil
from typing import Callable

cdef int g_level = LoggerLevel.NOT_SET
cdef object g_py_log

def py_callback_log(message: str):
    global g_py_log
    g_py_log(message)

def native_set_log_callback(logger_callback: Callable[[str], None]) -> None:
    global g_py_log
    g_py_log = logger_callback

def native_restore_log_callback() -> None:
    native_set_log_callback(print)

native_restore_log_callback()

cdef int can_log(LoggerLevel level) noexcept nogil:
    global g_py_log
    global g_level
    if level >= g_level:
        return 1
    return 0

cdef log_f log_error() noexcept nogil:
    if 1 == can_log(LoggerLevel.ERROR):
        return log_to_py_log
    return no_log

cdef log_f log_warning() noexcept nogil:
    if 1 == can_log(LoggerLevel.WARNING):
        return log_to_py_log
    return no_log

cdef log_f log_info() noexcept nogil:
    if 1 == can_log(LoggerLevel.INFO):
        return log_to_py_log
    return no_log

cdef log_f log_debug() noexcept nogil:
    if 1 == can_log(LoggerLevel.DEBUG):
        return log_to_py_log
    return no_log


cdef void set_logger_level(LoggerLevel level) noexcept nogil:
    global g_level
    g_level = level

cdef int no_log(const char* format, ...) noexcept nogil:
    pass

cdef char* format_var_args(const char* format_str, va_list args) noexcept nogil:
    cdef int size = vsnprintf(NULL, 0, format_str, args) + 1
    cdef char* buffer = <char*>malloc(size)
    if buffer is NULL:
        return NULL
    vsnprintf(buffer, size, format_str, args)
    return buffer

cdef int log_to_py_log(const char *format, ...) noexcept nogil:
    cdef va_list args
    cdef char* result
    va_start(args, format)
    result = format_var_args(format, args)
    va_end(args)
    if result != NULL:
        with gil:
            py_callback_log(result.decode('utf-8'))
        free(result)
    else:
        with gil:
            py_callback_log('format_var_args() returned NULL')
    return 0


def native_set_logger_level(int level) -> None:
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
